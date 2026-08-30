"""
Hallucination guard: evaluates RAG retrieval confidence and decides
whether the AI should answer, disclaim, or escalate to community.
"""
from typing import List, Dict, Any, Tuple


# Thresholds tuned for BOTH Gemini embeddings (high cosine similarity)
# AND local hash embeddings (lower absolute cosine scores).
# Hash embeddings typically score 0.10–0.40 for good matches, so we use
# a relative scale based on top_score rather than hard absolute cutoffs.
_HIGH_GEMINI   = 0.65   # Gemini embedding: clear match
_MED_GEMINI    = 0.35   # Gemini embedding: partial match
_HIGH_HASH     = 0.25   # Local hash embedding: clear match
_MED_HASH      = 0.10   # Local hash embedding: partial match


def _is_hash_embedding_score(top_score: float) -> bool:
    """
    Gemini embeddings produce cosine scores ≥ 0.5 for semantically similar
    text. Hash embeddings are capped ~0.45 even for perfect keyword matches.
    We treat anything < 0.50 as potentially a hash score.
    """
    return top_score < 0.50


def evaluate_confidence(matches: List[Dict[str, Any]]) -> Tuple[str, str, str]:
    """
    Returns (confidence_level, confidence_type, fallback_suffix).
    confidence_level: 'high' | 'medium' | 'low' | 'no_evidence'
    confidence_type:  'official_verified' | 'community_grounded' | 'no_evidence'
    fallback_suffix:  extra disclaimer text appended to the AI reply (empty string = none)
    """
    if not matches:
        return (
            "no_evidence",
            "no_evidence",
            "",  # caller decides the reply text when there are zero matches
        )

    top_score = float(matches[0].get("score", 0.0))
    source_type = matches[0].get("source_type", "official")
    conf_type = "community_grounded" if source_type == "community" else "official_verified"

    # Choose thresholds based on embedding regime
    if _is_hash_embedding_score(top_score):
        high_t, med_t = _HIGH_HASH, _MED_HASH
    else:
        high_t, med_t = _HIGH_GEMINI, _MED_GEMINI

    if top_score >= high_t:
        return ("high", conf_type, "")
    elif top_score >= med_t:
        return ("medium", conf_type, "")
    elif top_score > 0.0:
        # Low but non-zero — answer with a caveat instead of blocking
        suffix = (
            "\n\n⚠️ *Low-confidence match — this information may not be fully "
            "accurate. Please verify with official MAHE MIT sources.*"
        )
        return ("low", conf_type, suffix)
    else:
        return ("no_evidence", "no_evidence", "")
