"""Small, deterministic sentiment scorer for community content.

The score is intentionally explainable and runs locally: no student content is
sent to a third-party service merely to produce an operations dashboard.
"""
import re
from typing import Dict


POSITIVE_WORDS = {
    "amazing", "awesome", "best", "clear", "easy", "excellent", "good",
    "great", "helpful", "love", "nice", "perfect", "thanks", "useful",
    "wonderful", "happy", "glad", "smooth", "recommend",
}
NEGATIVE_WORDS = {
    "angry", "annoying", "awful", "bad", "broken", "confusing", "delay",
    "difficult", "disappointed", "frustrated", "hate", "issue", "poor",
    "problem", "sad", "terrible", "unfair", "urgent", "worst", "worry",
}
NEGATORS = {"not", "no", "never", "hardly", "isnt", "isn't", "wasnt", "wasn't"}


def analyze_sentiment(text: str) -> Dict[str, object]:
    """Return an explainable, normalized sentiment classification for text."""
    words = re.findall(r"[a-zA-Z']+", (text or "").lower())
    if not words:
        return {"label": "neutral", "score": 0.0, "positive_terms": 0, "negative_terms": 0}

    positive_terms = 0
    negative_terms = 0
    score = 0
    negate_for = 0
    for word in words:
        if word in NEGATORS:
            negate_for = 2
            continue
        direction = 1 if word in POSITIVE_WORDS else -1 if word in NEGATIVE_WORDS else 0
        if direction:
            if negate_for:
                direction *= -1
            if direction > 0:
                positive_terms += 1
            else:
                negative_terms += 1
            score += direction
        if negate_for:
            negate_for -= 1

    normalized = round(score / max(1, positive_terms + negative_terms), 3)
    label = "positive" if normalized >= 0.2 else "negative" if normalized <= -0.2 else "neutral"
    return {
        "label": label,
        "score": normalized,
        "positive_terms": positive_terms,
        "negative_terms": negative_terms,
    }
