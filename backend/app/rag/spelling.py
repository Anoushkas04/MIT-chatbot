"""Spelling correction for search queries, against the words in the indexed documents.

A misspelt word ("attendence", "chirstmas", "radhka") matches nothing in BM25 and pulls
the vector search off course. Each query word that isn't in the corpus vocabulary is
replaced by the closest corpus word: 1 edit for words up to 5 letters, 2 for longer ones,
counting a swap of two neighbouring letters as one edit (optimal string alignment).
Ties go to the more frequent word. Short words, numbers, codes and stopwords are left
alone, as is any word the documents already use (unless it's a one-off OCR misspelling of
a common word one edit away).
"""
import re
from collections import Counter, defaultdict
from functools import lru_cache

from rapidfuzz import process
from rapidfuzz.distance import OSA

from app.rag.text_norm import STOPWORDS, SYNONYMS, stem

WORD = re.compile(r"[a-z]+")
MIN_LENGTH = 4
# A word the corpus has at most this often is treated as a possible OCR misspelling…
RARE = 2
# …when a word one edit away is at least this much more frequent (and seen this often)
COMMON_RATIO, COMMON_MIN = 50, 20


@lru_cache
def vocabulary() -> tuple[Counter, dict]:
    """Word counts from the indexed chunks, plus the student phrasings text_norm understands."""
    from app.rag.store import get_store

    counts: Counter = Counter()
    for chunk in get_store().chunks:
        counts.update(WORD.findall(f"{chunk.get('retrieval_text', '')} {chunk.get('text', '')}".lower()))
    for phrase in SYNONYMS:  # "endsem", "midsem", "bunk": known words, never corrected
        counts.update(WORD.findall(phrase))
    by_length: dict = defaultdict(list)
    for word in counts:
        if len(word) >= MIN_LENGTH:  # never "correct" into a short word or acronym ("cabn" -> "can")
            by_length[len(word)].append(word)
    return counts, by_length


def clear_cache() -> None:
    vocabulary.cache_clear()


def correct_word(word: str) -> str | None:
    """The corpus word this one was probably meant to be, or None to leave it."""
    if len(word) < MIN_LENGTH or word in STOPWORDS:
        return None
    counts, by_length = vocabulary()
    seen = counts.get(word, 0)
    if seen > RARE or (stem(word) != word and counts.get(stem(word), 0) >= 2):  # "hostels" is fine if "hostel" is known
        return None
    max_edits = 1 if len(word) <= 5 or seen else 2
    pool = [w for n in range(len(word) - max_edits, len(word) + max_edits + 1) for w in by_length.get(n, ())]
    matches = process.extract(word, pool, scorer=OSA.distance, score_cutoff=max_edits, limit=20)
    candidates = [(dist, -counts[w], w) for w, dist, _ in matches if w != word]
    if seen:
        # The word exists but barely: only fix it towards a much more common neighbour
        candidates = [c for c in candidates if c[0] == 1 and -c[1] >= max(COMMON_MIN, COMMON_RATIO * seen)]
    if not candidates:
        return None
    return min(candidates)[2]


def correct_query(query: str) -> str:
    """The query with misspelt words replaced; everything else (case, punctuation) kept."""
    def fix(match: re.Match) -> str:
        original = match.group(0)
        corrected = correct_word(original.lower())
        if not corrected:
            return original
        return corrected.capitalize() if original[:1].isupper() else corrected

    return re.sub(r"[A-Za-z]+", fix, query)
