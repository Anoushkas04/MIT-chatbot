"""
Hallucination guard: evaluates RAG retrieval confidence and decides
whether the AI should answer, disclaim, or escalate to community.
"""
from typing import List, Dict, Any, Tuple


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

    # Hybrid retrieval scores are normalized reciprocal-rank fusion scores.
    if top_score >= 0.75:
        return ("high", conf_type, "")
    elif top_score >= 0.35:
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
