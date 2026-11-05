"""Keywords and a short summary for each indexed document, shown in Utilities > Documents.

Keywords: candidate phrases are runs of up to three content words between stopwords and
punctuation (as in RAKE), scored by TF-IDF across the corpus's documents, so phrases that
are frequent in this document but rare elsewhere rank first. Words the corpus has fewer
than three times are treated as OCR noise.

Summary: extractive and centroid-based: sentences from the start of the document are
scored by the TF-IDF weight of their words (length-normalised), and the best two are
shown in document order. No model is involved, so it runs during the index build.

    python -m app.rag.doc_insights      # rebuild from the current chunks.json
"""
import json
import math
import re
from collections import Counter, defaultdict

from app.rag.text_norm import STOPWORDS, index_tokens

INSIGHTS_FILE = "doc_insights.json"
KEYWORDS = 6
SUMMARY_SENTENCES = 2
MIN_CORPUS_COUNT = 3  # rarer words are mostly OCR noise
MAX_PHRASE_WORDS = 3
# Common English and document boilerplate on top of the retrieval stopwords
EXTRA_STOPWORDS = {
    "shall", "may", "also", "well", "per", "etc", "within", "without", "upon", "via", "whether", "however",
    "page", "pages", "table", "fig", "figure", "note", "notes", "total", "number", "following", "given",
    "used", "using", "based", "various", "one", "two", "three", "four", "five", "first", "second", "third",
    "new", "able", "include", "includes", "including", "required", "respective", "respectively", "concerned",
    "manipal", "mit", "mahe", "institute", "technology", "academy", "higher", "education", "university",
    "constituent", "unit", "dated", "date", "ref", "sd", "copy", "students", "student", "hereby",
    # textbook references, web-page furniture and table headers
    "wiley", "sons", "mcgraw", "hill", "tata", "pearson", "prentice", "hall", "springer", "elsevier", "oxford",
    "cengage", "press", "publishers", "publishing", "edition", "edn", "vol", "text", "book", "books", "chapter",
    "reference", "references", "cookie", "cookies", "website", "browsing", "experience", "privacy", "policy",
    "source", "name", "title", "abstract", "introduction", "agree", "continuing", "use",
    "edu", "com", "www", "http", "https", "tech", "btech", "official",
}
STOP = STOPWORDS | EXTRA_STOPWORDS
WORD = re.compile(r"[A-Za-z][A-Za-z'&-]*")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])|\n+")
ABBREVIATION_END = re.compile(r"\b[A-Za-z]{1,3}\.$")  # "Max.", "Dr.", "No." don't end a sentence


def _sentences(text: str) -> list[str]:
    out: list[str] = []
    for piece in SENTENCE_SPLIT.split(text):
        piece = piece.strip()
        if out and ABBREVIATION_END.search(out[-1]) and piece and "\n" not in piece:
            out[-1] = f"{out[-1]} {piece}"
        elif piece:
            out.append(piece)
    return out
REFERENCE = re.compile(r"\(\d+e\)|\b(19|20)\d\d\.\s*\d*\.?\s*$|publications?,|press,|india,|isbn", re.IGNORECASE)


def _words(text: str) -> list[str]:
    return [w.lower().strip("'-&") for w in WORD.findall(text)]


def _phrases(text: str, valid) -> list[tuple[str, str]]:
    """(key, display form) for each run of content words between stopwords/punctuation."""
    out = []
    for segment in re.split(r"[^A-Za-z'&\s-]+|\s-\s", text):
        run: list[str] = []
        for word in WORD.findall(segment):
            low = word.lower().strip("'-&")
            if low in STOP or not valid(low):
                if run:
                    out.append(run)
                run = []
            else:
                run.append(word.strip("'-&"))
        if run:
            out.append(run)
    phrases = []
    for run in out:
        for start in range(0, len(run), MAX_PHRASE_WORDS):
            piece = run[start:start + MAX_PHRASE_WORDS]
            phrases.append((" ".join(w.lower() for w in piece), " ".join(piece)))
    return phrases


# Extractive summaries only read well for prose. Course plans, syllabi, curricula and rank or
# fee tables give a random topic line or a textbook reference, so those show keywords only.
SUMMARY_TYPES = {"notice", "guidelines", "regulations", "document", "clubs", "academic_calendar", "sop", "handbook"}


def build_insights(records: list[dict]) -> dict[str, dict]:
    by_doc: dict[str, list[str]] = defaultdict(list)
    doc_type: dict[str, str] = {}
    for record in records:
        source = record.get("source_file") or record.get("source")
        if source:
            by_doc[source].append(str(record.get("text", "")))
            doc_type.setdefault(source, str(record.get("document_type") or "document"))
    corpus_counts: Counter = Counter()
    doc_words: dict[str, Counter] = {}
    for source, texts in by_doc.items():
        counts = Counter(_words(" ".join(texts)))
        doc_words[source] = counts
        corpus_counts.update(counts)
    n_docs = len(by_doc)
    doc_freq = Counter(w for counts in doc_words.values() for w in counts)

    def valid(word: str) -> bool:
        return len(word) >= 3 and corpus_counts[word] >= MIN_CORPUS_COUNT and word.isalpha()

    def idf(word: str) -> float:
        return math.log((1 + n_docs) / (1 + doc_freq[word])) + 1

    # Sentences repeated across chunks are letterheads, footers or cookie notices
    sentence_counts: Counter = Counter(
        " ".join(s.lower().split()) for texts in by_doc.values() for text in texts for s in _sentences(text)
    )

    insights = {}
    for source, texts in by_doc.items():
        counts = doc_words[source]
        total = sum(counts.values()) or 1
        weight = {w: (c / total) * idf(w) for w, c in counts.items() if w not in STOP and valid(w)}

        phrase_counts: Counter = Counter()
        display: dict[str, Counter] = defaultdict(Counter)
        for text in texts:
            for key, shown in _phrases(text, valid):
                phrase_counts[key] += 1
                display[key][shown] += 1
        min_freq = 2 if total > 400 else 1
        scored = []
        for key, freq in phrase_counts.items():
            if freq < min_freq:
                continue
            tokens = key.split()
            score = sum(weight.get(t, 0.0) for t in tokens) * math.log(1 + freq) * (1 + 0.3 * (len(tokens) - 1))
            if score > 0:
                scored.append((score, key))
        keywords, covered = [], set()
        for _, key in sorted(scored, reverse=True):
            tokens = set(index_tokens(key)) or set(key.split())  # stems: "drive" and "drives" are one
            if tokens <= covered:
                continue  # already said by another phrase
            shown = display[key].most_common(1)[0][0]
            keywords.append(shown if not shown.isupper() or len(shown) <= 5 else shown.title())
            covered |= tokens
            if len(keywords) == KEYWORDS:
                break

        sentences, seen = [], []
        for position, sentence in enumerate(s.strip() for text in texts[:6] for s in _sentences(text)):
            norm = " ".join(sentence.lower().split())
            if sentence_counts[norm] > 1 or norm.startswith("source:") or any(norm in o or o in norm for o in seen):
                continue  # boilerplate, or already seen through the chunk overlap
            seen.append(norm)
            # Whole sentences only: chunk boundaries cut sentences, and a fragment reads badly
            if not re.match(r"[A-Z0-9]", sentence) or not re.search(r"[.!?]$", sentence) or REFERENCE.search(sentence):
                continue
            words = _words(sentence)
            if len(words) < 8:
                continue
            digits = sum(ch.isdigit() for ch in sentence)
            if not (40 <= len(sentence) <= 260) or len(words) < 6 or digits > 0.2 * len(sentence):
                continue
            if sum(1 for w in words if valid(w) or w in STOP) < 0.8 * len(words):
                continue  # mostly OCR noise
            score = sum(weight.get(w, 0.0) for w in set(words)) / math.sqrt(len(words))
            sentences.append((score, position, " ".join(sentence.split())))
        best = sorted(sorted(sentences, reverse=True)[:SUMMARY_SENTENCES], key=lambda s: s[1]) if doc_type[source] in SUMMARY_TYPES else []
        insights[source] = {"keywords": keywords, "summary": " ".join(s for _, _, s in best)[:400]}
    return insights


def load() -> dict[str, dict]:
    from app.config import DATA_DIR

    path = DATA_DIR / INSIGHTS_FILE
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError):
        return {}


if __name__ == "__main__":
    from app.config import DATA_DIR

    chunks = json.loads((DATA_DIR / "chunks.json").read_text(encoding="utf-8"))
    result = build_insights(chunks)
    (DATA_DIR / INSIGHTS_FILE).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote insights for {len(result)} documents")
