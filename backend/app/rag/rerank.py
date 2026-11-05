"""Second-stage re-ranking with an absolute relevance score.

Fused retrieval scores are relative (the top result is always 1.0), so they can't say
"nothing here answers this". Each candidate passage gets a relevance score: the share
of the question's content words it contains, weighted by how rare each word is in the
corpus (BM25 idf; words the corpus never uses weigh the most). Synonyms from text_norm
count as matches. Candidates are re-ordered by relevance blended with the fused rank,
and the best relevance feeds the answer's confidence (chat_router).
"""
from functools import lru_cache

from app.rag.text_norm import SYNONYMS, index_tokens

# Words that say little about what the question is about
QUESTION_NOISE = {
    "mit", "manipal", "mahe", "student", "college", "campus", "university", "official", "please",
    # Conversational filler: says how something is asked, not what about
    "happen", "mean", "below", "above", "under", "over", "less", "within", "regard", "regarding",
    "explain", "describe", "according", "revis", "current", "currently", "exactly", "actually",
}
BLEND = 0.65  # weight of relevance against the fused retrieval score


@lru_cache
def _idf() -> tuple[dict, float]:
    from app.rag.keyword_store import get_keyword_store

    idf = get_keyword_store().index.idf
    return idf, max(idf.values()) if idf else 1.0


@lru_cache
def _alternatives() -> dict[str, set[str]]:
    """Each word of a synonym phrase -> the document words it stands for ("fest" -> revels,
    "seventy-five" -> 75), from the same lists the search expands queries with."""
    from app.rag.hybrid import QUERY_ALIASES, QUERY_REWRITES

    alts: dict[str, set[str]] = {}
    for phrase, expansion in {**SYNONYMS, **QUERY_REWRITES, **QUERY_ALIASES}.items():
        targets = set(index_tokens(expansion))
        for token in index_tokens(phrase):
            alts.setdefault(token, set()).update(targets)
    return alts


def clear_cache() -> None:
    _idf.cache_clear()


def query_terms(query: str) -> list[tuple[str, float, set[str]]]:
    """(term, weight, words that also count as a match) for each content word of the question."""
    idf, top = _idf()
    alts = _alternatives()
    terms, seen = [], set()
    for token in index_tokens(query):
        if token in QUESTION_NOISE or token in seen or (token.isdigit() and len(token) == 4 and 2015 <= int(token) <= 2030):
            continue
        seen.add(token)
        # A word the corpus never uses is the strongest sign the documents can't answer
        weight = idf.get(token, top * 1.25)
        terms.append((token, max(weight, 0.1), alts.get(token, set())))
    return terms


def relevance(terms: list[tuple[str, float, set[str]]], record: dict) -> float:
    if not terms:
        return 0.0
    words = set(index_tokens(" ".join(str(record.get(k, "")) for k in ("source_file", "retrieval_text", "text"))))
    total = sum(w for _, w, _ in terms)
    covered = sum(w for t, w, alt in terms if t in words or alt & words)
    return covered / total


def rerank(query: str, matches: list[dict]) -> list[dict]:
    """Matches re-ordered by blended relevance, each with a 'relevance' score (0-1)."""
    terms = query_terms(query)
    scored = []
    for rank, match in enumerate(matches):
        rel = relevance(terms, match)
        prior = float(match.get("score", 0.0))
        scored.append((BLEND * rel + (1 - BLEND) * prior, -rank, {**match, "relevance": round(rel, 4)}))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [m for _, _, m in scored]


def best_relevance(query: str, matches: list[dict]) -> float:
    terms = query_terms(query)
    return max((relevance(terms, m) for m in matches), default=0.0)
