"""Shared text normalisation for retrieval: tokens, stopwords, light stemming and
campus synonyms.

Both the BM25 index and the local hash embeddings tokenise with `index_tokens`, so
question words ("what", "how", "do I") no longer match FAQ pages on their own, and
"exams"/"exam" or "holidays"/"holiday" match each other. `expand_query` adds the words
the documents actually use for common student phrasings ("cultural fest" -> REVELS).
"""
import re

STOPWORDS = {
    "a", "about", "after", "all", "also", "am", "an", "and", "any", "are", "as", "at", "be",
    "been", "before", "being", "but", "by", "can", "could", "did", "do", "does", "doing", "for",
    "from", "get", "got", "had", "has", "have", "he", "her", "here", "him", "his", "how", "i",
    "if", "in", "into", "is", "it", "its", "just", "let", "me", "might", "mine", "more", "most",
    "must", "my", "need", "no", "not", "of", "on", "or", "our", "out", "please", "she", "should",
    "so", "some", "such", "tell", "than", "that", "the", "their", "them", "then", "there", "these",
    "they", "this", "those", "to", "up", "us", "was", "we", "were", "what", "whats", "when",
    "where", "which", "while", "who", "whom", "why", "will", "with", "would", "you", "your",
    "know", "want", "give", "show", "list", "explain", "describe", "say", "says", "much", "many",
}

# Student phrasing -> words used in the official documents. Keys are matched as whole
# words/phrases in the lowercased query; values are appended to the search query.
SYNONYMS = {
    "cultural fest": "revels",
    "culture fest": "revels",
    "tech fest": "techtatva tech tatva",
    "technical fest": "techtatva tech tatva",
    "fest": "revels techtatva festival",
    "festival": "revels techtatva fest",
    "holiday": "holiday holidays vacation",
    "holidays": "holiday vacation",
    "vacation": "holiday vacation",
    "leave": "holiday leave",
    "break": "holiday vacation",
    "end sem": "end semester examination",
    "endsem": "end semester examination",
    "end-sem": "end semester examination",
    "mid sem": "mid-term examination",
    "midsem": "mid-term examination",
    "mid-sem": "mid-term examination",
    "midterm": "mid-term examination",
    "exam": "examination",
    "exams": "examination",
    "test": "examination test",
    "fail": "failure f grade makeup re-registration backlog",
    "failed": "failure f grade makeup re-registration backlog",
    "failing": "failure f grade makeup re-registration backlog",
    "backlog": "re-registration f grade makeup",
    "arrear": "re-registration f grade makeup",
    "supplementary": "makeup examination",
    "retest": "re-test mid-term",
    "re-test": "mid-term re-test",
    "gpa": "gpa grade point average grade points",
    "cgpa": "cgpa cumulative grade point average",
    "sgpa": "gpa grade point average",
    "grade": "grade points letter grade",
    "bunk": "attendance",
    "attendance": "attendance 75%",
    "shortage": "attendance shortage detained",
    "debarred": "attendance detained",
    "coding": "programming software developers computing",
    "programming": "programming software developers computing",
    "developer": "developers software programming",
    "robotics": "robotics robot automation mechatronics",
    "robot": "robotics automation mechatronics",
    "ai": "artificial intelligence machine learning",
    "dance": "dance crew",
    "music": "music band",
    "drama": "dramatics theatre",
    "theatre": "dramatics theatre",
    "photography": "photography",
    "debate": "debate literary quiz",
    "space": "astronomy",
    "startup": "entrepreneurship enactus",
    "internship": "internship ilpps",
    "placement": "placement ilpps",
    "job": "placement",
    "jobs": "placement",
    "fee": "fee fees payment",
    "fees": "fee payment",
    "pay": "payment fee",
    "scholarship": "scholarship ssp",
    "director": "director director-in-charge",
    "branch change": "branch change",
    "re-registration": "re-registration re-register",
    "reregistration": "re-registration re-register",
    "cheating": "malpractice",
    "copying": "malpractice",
    "hall ticket": "admit card hall ticket",
}

_SUFFIXES = (("ies", "y"), ("sses", "ss"), ("ing", ""), ("es", ""), ("ed", ""), ("s", ""))


def stem(token: str) -> str:
    """A deliberately light stemmer: plurals and -ing/-ed, never below four letters."""
    if len(token) <= 4 or token.isdigit():
        return token
    for suffix, replacement in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) + len(replacement) >= 4:
            if suffix == "es" and not token.endswith(("ches", "shes", "xes", "zes", "oes")):
                continue  # "courses" -> "course" via the plain "s" rule below
            if suffix == "s" and token.endswith(("ss", "us", "is")):
                return token
            return token[: len(token) - len(suffix)] + replacement
    return token


def raw_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def index_tokens(text: str) -> list[str]:
    """Tokens used for retrieval: lowercase, no stopwords, lightly stemmed."""
    return [stem(t) for t in raw_tokens(text) if len(t) > 1 and t not in STOPWORDS]


def expand_query(query: str) -> str:
    """The query plus the document vocabulary for any student phrasings it contains."""
    lowered = " " + " ".join(re.sub(r"[^a-z0-9\- ]+", " ", (query or "").lower()).split()) + " "
    additions = [words for phrase, words in SYNONYMS.items() if f" {phrase} " in lowered]
    return f"{query} {' '.join(additions)}".strip() if additions else query
