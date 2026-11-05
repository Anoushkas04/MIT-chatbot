import hashlib
import os
import re
import time
import numpy as np

from google import genai
from google.genai import errors, types

from app.config import (
    CHAT_MODEL,
    EMBEDDING_MODEL,
    GEMINI_API_KEY,
    GEMINI_EMBEDDING_API_KEY,
    GEMINI_EMBEDDINGS_ENABLED,
    LLM_TIMEOUT_SECONDS,
)

_client = None


def is_valid_key(key: str) -> bool:
    if not key or key.strip() in ("your_gemini_api_key_here", "your_google_gemini_api_key_here"):
        return False
    return len(key.strip()) > 8


def get_client() -> genai.Client:
    global _client
    import os
    current_key = os.environ.get("GEMINI_API_KEY", "") or GEMINI_API_KEY
    if not is_valid_key(current_key):
        raise RuntimeError("GEMINI_API_KEY is not set (see backend/.env.example)")
    return genai.Client(
        api_key=current_key.strip(),
        http_options=types.HttpOptions(timeout=int(LLM_TIMEOUT_SECONDS * 1000)),
    )


HASH_EMBED_DIM = 768
# v2: stopwords removed and light stemming (app/rag/text_norm.py); v1 indexes need a rebuild
LOCAL_EMBEDDER = "local-hash-v2"
# Build-time Gemini embedding limits. The free tier allows 30,000 tokens and 100 requests a
# minute: requests stay small and paced under that, and one build spends at most
# EMBED_BUILD_SECONDS embedding (the rest continues on the next build, see embedding_cache).
EMBED_BATCH_SIZE = 100
EMBED_REQUEST_TOKENS = int(os.environ.get("EMBED_REQUEST_TOKENS", "9000"))
EMBED_TOKENS_PER_MINUTE = int(os.environ.get("EMBED_TOKENS_PER_MINUTE", "25000"))
EMBED_BUILD_SECONDS = int(os.environ.get("EMBED_BUILD_SECONDS", "900"))
# A question's embedding is on the chat's critical path; don't let it hang a reply
QUERY_EMBED_TIMEOUT_MS = 10_000


def active_embedder() -> str:
    """The embedder a build would use now: Gemini only when enabled AND keyed."""
    if GEMINI_EMBEDDINGS_ENABLED and is_valid_key(GEMINI_EMBEDDING_API_KEY):
        return f"gemini:{EMBEDDING_MODEL}"
    return LOCAL_EMBEDDER




def _hash_embed(text: str, dim: int = HASH_EMBED_DIM) -> list[float]:
    """
    Improved local embedding using TF-IDF-style unigram + bigram hashing with
    position weighting. Produces much better retrieval than simple unigrams.
    """
    from app.rag.text_norm import index_tokens

    vec = np.zeros(dim, dtype=np.float32)
    # Stopwords dropped and plurals folded, so question words don't dominate the vector
    tokens = index_tokens(text)
    if not tokens:
        return vec.tolist()

    total = len(tokens)
    # Unigrams with position-based IDF-like weighting
    for pos, word in enumerate(tokens):
        # position weight: words near the start/end carry slightly more weight
        pos_w = 1.0 + 0.3 * (1.0 - abs(pos / max(total - 1, 1) - 0.5) * 2)
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        sign = 1.0 if (h & 1) == 0 else -1.0
        vec[h % dim] += sign * pos_w

    # Bigrams (pairs of consecutive tokens)
    for i in range(len(tokens) - 1):
        bigram = tokens[i] + "_" + tokens[i + 1]
        h = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
        sign = 1.0 if (h & 1) == 0 else -1.0
        vec[h % dim] += sign * 1.5  # bigrams weighted higher

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    return embed_texts_labelled(texts)[0]


def _embedding_client(timeout_ms: int | None = None) -> genai.Client:
    """Gemini client for embeddings: GEMINI_EMBEDDING_API_KEY if set, otherwise GEMINI_API_KEY."""
    return genai.Client(
        api_key=GEMINI_EMBEDDING_API_KEY.strip(),
        http_options=types.HttpOptions(timeout=timeout_ms or int(LLM_TIMEOUT_SECONDS * 1000)),
    )


def estimate_tokens(text: str) -> int:
    """A cautious token count for rate limiting (~3.5 characters a token)."""
    return max(1, int(len(text) / 3.5) + 1)


class _TokenPacer:
    """Keeps requests under a tokens-per-minute budget by waiting when the last minute is full."""

    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.sent: list[tuple[float, int]] = []

    def wait_for(self, tokens: int) -> None:
        while True:
            now = time.monotonic()
            self.sent = [(t, n) for t, n in self.sent if now - t < 60]
            if sum(n for _, n in self.sent) + tokens <= self.per_minute or not self.sent:
                self.sent.append((now, tokens))
                return
            time.sleep(max(0.5, 60 - (now - self.sent[0][0])))


def _token_batches(texts: list[str]) -> list[list[str]]:
    batches, batch, size = [], [], 0
    for text in texts:
        tokens = estimate_tokens(text)
        if batch and (size + tokens > EMBED_REQUEST_TOKENS or len(batch) >= EMBED_BATCH_SIZE):
            batches.append(batch)
            batch, size = [], 0
        batch.append(text)
        size += tokens
    if batch:
        batches.append(batch)
    return batches


# Filled in by embed_texts_labelled for the index manifest (shown in /api/health)
last_embedding_progress: dict = {}


def embed_texts_labelled(texts: list[str], api_texts: list[str] | None = None) -> tuple[list[list[float]], str]:
    """Vectors plus the embedder that actually produced them. Gemini and the local hash
    embedder both return 768 numbers, so the label is the only way an index can record
    that a failed Gemini call fell back to local vectors.

    `api_texts` is what's sent to Gemini (a shorter form of each text, "" to skip it: that
    record gets an empty vector). Gemini's free tier allows 30,000 embedding tokens a
    minute and the corpus is ~2M tokens, so requests are token-sized and paced, every batch
    is saved to the cache as it arrives, and a build stops after EMBED_BUILD_SECONDS: until
    every text is cached the index stays on local vectors, and the next build carries on."""
    last_embedding_progress.clear()
    if not GEMINI_EMBEDDINGS_ENABLED or not is_valid_key(GEMINI_EMBEDDING_API_KEY):
        print("Using local hash embeddings. Set GEMINI_EMBEDDINGS_ENABLED=true and rebuild the index to use Gemini embeddings.")
        return [_hash_embed(t) for t in texts], LOCAL_EMBEDDER
    from app.rag import embedding_cache

    api_texts = list(api_texts) if api_texts is not None else list(texts)
    wanted = list(dict.fromkeys(t for t in api_texts if t))
    cached = embedding_cache.load(EMBEDDING_MODEL, wanted)
    missing = [t for t in wanted if embedding_cache.key_for(EMBEDDING_MODEL, t) not in cached]
    total_tokens = sum(estimate_tokens(t) for t in missing)
    print(f"Gemini embeddings: {len(wanted) - len(missing)} of {len(wanted)} texts already embedded; "
          f"{len(missing)} to go (~{total_tokens:,} tokens).")
    started = time.monotonic()
    pacer = _TokenPacer(EMBED_TOKENS_PER_MINUTE)
    done = len(wanted) - len(missing)
    try:
        client = _embedding_client()
        for batch in _token_batches(missing):
            pacer.wait_for(sum(estimate_tokens(t) for t in batch))
            # Checked after waiting for the token budget, so a wait can't run the build over its limit
            if time.monotonic() - started > EMBED_BUILD_SECONDS:
                print(f"Gemini embeddings: stopping after {EMBED_BUILD_SECONDS // 60} minutes with "
                      f"{done} of {len(wanted)} embedded; the next build continues.")
                break
            vectors = _embed_batch(client, batch)
            embedding_cache.save(EMBEDDING_MODEL, batch, vectors)  # kept even if a later batch fails
            cached.update({embedding_cache.key_for(EMBEDDING_MODEL, t): v for t, v in zip(batch, vectors)})
            done += len(batch)
    except Exception as err:
        print(f"Gemini embedding notice: {err}. Using local feature hash embeddings.")
    last_embedding_progress.update({"embedded": done, "needed": len(wanted)})
    if done < len(wanted):
        # Never a mixed index: local vectors until every text has a Gemini vector
        return [_hash_embed(t) for t in texts], LOCAL_EMBEDDER
    print("Gemini embeddings: complete.")
    zero = [0.0] * 768
    return [cached[embedding_cache.key_for(EMBEDDING_MODEL, t)] if t else zero for t in api_texts], f"gemini:{EMBEDDING_MODEL}"


def _embed_batch(client, batch: list[str]) -> list[list[float]]:
    """One request for the batch; if the API rejects its size, retry in smaller pieces."""
    try:
        return _embed_batch_with_retry(client, batch)
    except errors.ClientError as e:
        if e.code == 400 and len(batch) > 20:
            return [v for i in range(0, len(batch), 20) for v in _embed_batch_with_retry(client, batch[i : i + 20])]
        raise


def _embed_batch_with_retry(client, batch, max_retries=6):
    for attempt in range(max_retries):
        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(output_dimensionality=768),
            )
            return [e.values for e in response.embeddings]
        except errors.ClientError as e:
            # A used-up daily quota won't recover in minutes: give up so the build falls back now
            if e.code == 429 and "PerDay" not in str(e) and attempt < max_retries - 1:
                wait = 40
                print(f"  rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait)
                continue
            raise


def embed_query(text: str, index_embedder: str | None = None) -> list[float]:
    """Embed a question with the embedder the index was built with (its manifest label).

    A question embedded by one model can't be compared with an index built by another, so a
    local-hash index always gets local vectors (no API call) and a Gemini index gets one quick
    Gemini call with no retries; if that fails the caller skips vector search for this question.
    """
    if not index_embedder or index_embedder.startswith("local-hash"):
        return _hash_embed(text)
    if not is_valid_key(GEMINI_EMBEDDING_API_KEY):
        raise RuntimeError("The index uses Gemini embeddings but no Gemini key is configured.")
    client = _embedding_client(timeout_ms=QUERY_EMBED_TIMEOUT_MS)
    response = client.models.embed_content(
        model=index_embedder.split(":", 1)[-1],
        contents=[text],
        config=types.EmbedContentConfig(output_dimensionality=768),
    )
    return response.embeddings[0].values


def synthesize_local_concise_answer(message: str, kb_part: str) -> str:
    """Create a conservative extractive answer using retrieved evidence only."""
    clean_lines: list[str] = []
    for raw_line in kb_part.splitlines():
        line = raw_line.strip()
        if (
            not line
            or line.startswith("[Source")
            or line.startswith("Grounding")
            or line.startswith("---")
            or len(line) < 12
        ):
            continue
        clean_lines.append(line)

    if not clean_lines:
        return (
            "I could not find enough indexed evidence to answer that reliably. "
            "Try a more specific question or ask the student community."
        )

    query_terms = {
        word for word in re.findall(r"\w+", message.lower())
        if len(word) > 2 and word not in {"where", "what", "when", "which", "with", "find", "can", "the", "for"}
    }
    ranked = sorted(
        clean_lines,
        key=lambda line: sum(term in line.lower() for term in query_terms),
        reverse=True,
    )
    relevant = [line for line in ranked if any(term in line.lower() for term in query_terms)]
    evidence = " ".join((relevant or ranked)[:3])
    if len(evidence) > 700:
        evidence = evidence[:697].rstrip() + "..."
    return f"Based on the retrieved campus sources: {evidence}"


def chat(system_instruction: str, history: list[dict], message: str) -> str:
    if not is_valid_key(GEMINI_API_KEY):
        if "RETRIEVED KNOWLEDGE BASE:\n" in system_instruction:
            kb_part = system_instruction.split("RETRIEVED KNOWLEDGE BASE:\n")[1].strip()
            if kb_part and kb_part != "No direct match found in indexed vector knowledge base.":
                ans = synthesize_local_concise_answer(message, kb_part)
                return ans
        return (
            "I couldn't find reliable information about this in official university documents.\n\n"
            "You can ask the Student Community in the Student Corner for peer insights!"
        )

    try:
        client = get_client()
        import os
        active_model = os.environ.get("GEMINI_MODEL", os.environ.get("CHAT_MODEL", CHAT_MODEL))
        contents = [types.Content(role=turn["role"], parts=[types.Part.from_text(text=turn["text"])]) for turn in history]
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

        response = client.models.generate_content(
            model=active_model,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_instruction),
        )
        return response.text
    except Exception as err:
        print(f"Gemini API call exception: {err}")
        if "RETRIEVED KNOWLEDGE BASE:\n" in system_instruction:
            kb_part = system_instruction.split("RETRIEVED KNOWLEDGE BASE:\n")[1].strip()
            if kb_part and kb_part != "No direct match found in indexed vector knowledge base.":
                return synthesize_local_concise_answer(message, kb_part)
        return (
            "I couldn't find reliable information about this in official university documents.\n\n"
            "You can ask the Student Community in the Student Corner for peer insights!"
        )

