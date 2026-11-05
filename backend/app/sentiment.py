"""Sentiment of a student's message, for the admin Insights page.

Polarity comes from VADER (a lexicon of ~7,500 scored words with rules for negation
"isn't fair", intensifiers "really bad", contrast "good but..." and punctuation).
Urgent, Confused and Frustrated are about what the student needs, not just tone, so
they come from cue phrases, gated by VADER's score so "cleared up my doubt" isn't
read as confusion.
"""
import re
from functools import lru_cache

URGENT = re.compile(r"\b(urgent|urgently|emergency|asap|immediately|right now|deadline (is )?today|closes tonight|"
                    r"in (an|one|\d+) (hour|hours|minutes?|mins?)|exam is tomorrow|quickly)\b")
FRUSTRATED = re.compile(r"\b(fed up|sick of|tired of|so done|ridiculous|annoying|nobody|no one is|no response|"
                        r"no reply|never works?|nothing .{0,20}works?|keeps (happening|crashing|logging)|again|"
                        r"every time|stuck|still (no|pending|not)|\d+ (days|times)|five times|seriously)\b")
CONFUSED = re.compile(r"\b(confused|confusing|don'?t (understand|get)|not sure|unclear|doubt|lost|"
                      r"what does .{1,30} mean|what is the difference|explain)\b")


@lru_cache
def _analyzer():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    return SentimentIntensityAnalyzer()


def classify(text: str) -> str:
    """One of Urgent, Frustrated, Confused, Negative, Positive, Neutral."""
    lowered = " ".join((text or "").lower().split())
    compound = _analyzer().polarity_scores(text or "")["compound"]
    if URGENT.search(lowered):
        return "Urgent"
    if FRUSTRATED.search(lowered) and compound < 0.2:
        return "Frustrated"
    if CONFUSED.search(lowered) and compound < 0.4:
        return "Confused"
    if compound <= -0.05:
        return "Negative"
    if compound >= 0.05:
        return "Positive"
    return "Neutral"
