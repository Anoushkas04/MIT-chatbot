import hashlib
import re
import time
import numpy as np

from google import genai
from google.genai import errors, types

from app.config import (
    CHAT_MODEL,
    EMBEDDING_MODEL,
    GEMINI_API_KEY,
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
# Texts per embedding request at build time. Fewer, larger requests stay further under the
# free tier's 100 requests a minute and 1,000 a day.
EMBED_BATCH_SIZE = 100
# A question's embedding is on the chat's critical path; don't let it hang a reply
QUERY_EMBED_TIMEOUT_MS = 10_000


def active_embedder() -> str:
    """The embedder a build would use now: Gemini only when enabled AND keyed."""
    if GEMINI_EMBEDDINGS_ENABLED and is_valid_key(GEMINI_API_KEY):
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


def embed_texts_labelled(texts: list[str]) -> tuple[list[list[float]], str]:
    """Vectors plus the embedder that actually produced them. Gemini and the local hash
    embedder both return 768 numbers, so the label is the only way an index can record
    that a failed Gemini call fell back to local vectors."""
    if not GEMINI_EMBEDDINGS_ENABLED or not is_valid_key(GEMINI_API_KEY):
        print("Using local hash embeddings. Set GEMINI_EMBEDDINGS_ENABLED=true and rebuild the index to use Gemini embeddings.")
        return [_hash_embed(t) for t in texts], LOCAL_EMBEDDER
    from app.rag import embedding_cache

    # Reuse what earlier builds embedded; only new or changed chunks spend the daily quota
    cached = embedding_cache.load(EMBEDDING_MODEL, texts)
    missing = [t for t in dict.fromkeys(texts) if embedding_cache.key_for(EMBEDDING_MODEL, t) not in cached]
    print(f"Gemini embeddings: {len(texts) - len(missing)} chunks from the cache, {len(missing)} to embed.")
    try:
        client = get_client()
        for i in range(0, len(missing), EMBED_BATCH_SIZE):
            batch = missing[i : i + EMBED_BATCH_SIZE]
            vectors = _embed_batch(client, batch)
            embedding_cache.save(EMBEDDING_MODEL, batch, vectors)  # kept even if a later batch fails
            cached.update({embedding_cache.key_for(EMBEDDING_MODEL, t): v for t, v in zip(batch, vectors)})
        return [cached[embedding_cache.key_for(EMBEDDING_MODEL, t)] for t in texts], f"gemini:{EMBEDDING_MODEL}"
    except Exception as err:
        print(f"Gemini embedding notice: {err}. Using local feature hash embeddings.")
        # Every text is re-embedded locally, so an index is never a mix of the two. The batches
        # that did succeed stay in the cache, so the next build only embeds the rest.
        return [_hash_embed(t) for t in texts], LOCAL_EMBEDDER


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
    if not is_valid_key(GEMINI_API_KEY):
        raise RuntimeError("The index uses Gemini embeddings but no Gemini key is configured.")
    client = genai.Client(
        api_key=GEMINI_API_KEY.strip(),
        http_options=types.HttpOptions(timeout=QUERY_EMBED_TIMEOUT_MS),
    )
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

