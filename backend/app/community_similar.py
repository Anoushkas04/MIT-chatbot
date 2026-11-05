"""Finding Community questions that are probably the same as a draft.

TF-IDF cosine similarity between the draft and each existing question (title counted
twice, since it carries the question). Words go through the same normalisation as chat
search (spelling correction, synonyms, stopwords, stemming) and are weighted by rarity
in the indexed documents, so "attendence" matches "attendance" and "fest" matches
"Revels", while common words count for little.
"""
import math
from collections import Counter

from app import models
from app.rag.spelling import correct_query
from app.rag.text_norm import index_tokens

DUPLICATE_MIN = 0.30  # cosine similarity at which a question is shown as a possible duplicate
# …and they must share at least this many words: one rare word in common ("attendance" in a mess
# question and an attendance-rule question) isn't the same question
MIN_SHARED = 2
TITLE_WEIGHT = 2


def _weights(title: str, body: str) -> dict[str, float]:
    from app.rag.hybrid import _expanded_query as expand_query  # synonyms, acronyms ("operating systems" -> OS), rewrites
    from app.rag.rerank import _idf

    idf, top = _idf()
    counts: Counter = Counter()
    for _ in range(TITLE_WEIGHT):
        counts.update(index_tokens(expand_query(correct_query(title or ""))))
    counts.update(index_tokens(expand_query(correct_query(body or ""))))
    return {t: (1 + math.log(n)) * idf.get(t, top) for t, n in counts.items()}


def _own_words(title: str, body: str) -> set[str]:
    """Words as written (spelling corrected), before synonyms add shared extras like "75"."""
    return set(index_tokens(correct_query(f"{title} {body}")))


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    dot = sum(w * b[t] for t, w in a.items() if t in b)
    norm = math.sqrt(sum(w * w for w in a.values())) * math.sqrt(sum(w * w for w in b.values()))
    return dot / norm if norm else 0.0


def similar_posts(db, title: str, body: str = "", limit: int = 3) -> list[dict]:
    draft = _weights(title, body)
    if not draft:
        return []
    draft_words = _own_words(title, body)
    posts = db.query(models.CommunityPost).filter(models.CommunityPost.deleted_at.is_(None)).all()
    scored = []
    for p in posts:
        if len(draft_words & _own_words(p.title, p.body)) >= MIN_SHARED:
            scored.append((round(_cosine(draft, _weights(p.title, p.body)), 3), p))
    scored.sort(key=lambda x: -x[0])
    answers = Counter(
        post_id for (post_id,) in db.query(models.CommunityComment.post_id).filter(
            models.CommunityComment.parent_id.is_(None), models.CommunityComment.deleted_at.is_(None)
        )
    ) if scored else Counter()
    return [
        {"id": str(p.id), "title": p.title, "score": score, "answers": answers.get(p.id, 0), "verified": bool(p.verified)}
        for score, p in scored[:limit] if score >= DUPLICATE_MIN
    ]
