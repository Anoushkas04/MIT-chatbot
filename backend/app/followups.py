"""Follow-up question suggestions, checked against the answer's own evidence.

The answer model is asked for a few follow-ups in the same call (prompts.py), so they
cost no extra request; they're split off the answer here. When there are none (local
mode, or the model skipped them), suggestions are built from the evidence itself:
calendar months, club details, faculty records, and other topics in the cited passage.
Every suggestion must be well covered by the same evidence (rerank.relevance) so it can
actually be answered, and must not repeat the question.
"""
import re
from functools import lru_cache

from app.rag.rerank import query_terms, relevance
from app.rag.text_norm import index_tokens

MAX_FOLLOWUPS = 3
MIN_COVERAGE = 0.5
FOLLOWUP_MARKER = re.compile(r"\n+\s*\**\s*follow[- ]?up questions?\s*\**\s*:\s*(.+)\Z", re.IGNORECASE | re.DOTALL)
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]


def split_model_followups(text: str) -> tuple[str, list[str]]:
    """The answer without its trailing "Follow-up questions: a | b | c" line, and those questions."""
    match = FOLLOWUP_MARKER.search(text or "")
    if not match:
        return text, []
    questions = [q.strip(" -•*\t\"") for q in re.split(r"\s*\|\s*|\n+", match.group(1))]
    return text[: match.start()].rstrip(), [q for q in questions if q]


def _title(source: str) -> str:
    """A readable document name: 'PLACEMENT GUIDELINES 13 JULY 2024 FINAL_250905_124353.pdf' -> 'Placement Guidelines'."""
    stem = re.sub(r"\.(pdf|docx|csv|md|txt)$", "", source or "", flags=re.IGNORECASE)
    stem = re.sub(r"[_]+|--+|\s-\s|\(\d+\)", " ", stem)
    words = [w for w in stem.split() if not re.fullmatch(r"\d{5,}|final|revised|compressed\.*|copy|-", w, re.IGNORECASE)]
    # Drop a trailing date ("13 JULY 2024") but keep a year that names an edition ("Handbook 2024")
    text = re.sub(r"\s\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}$",
                  "", " ".join(words), flags=re.IGNORECASE)
    text = text.replace("Hand Book", "Handbook")
    return text.title() if text.isupper() else text


def _calendar_suggestions(evidence: dict) -> list[str]:
    months = re.findall(r"\b(20\d\d)-(\d\d)-\d\d\b", evidence.get("text", ""))
    out = []
    for year, month in dict.fromkeys(months):
        out.append(f"What is on the academic calendar in {MONTH_NAMES[int(month) - 1]} {year}?")
    return out[:2]


def _club_suggestions(evidence: dict) -> list[str]:
    name = str(evidence.get("source", "")).replace(" (official club page)", "")
    category = "technical" if "— Technical club" in evidence.get("text", "") else "non-technical"
    return [f"What is the official email of {name}?", f"List all the {category} clubs at MIT Manipal"]


def _faculty_suggestions(lookup: dict) -> list[str]:
    records = lookup.get("records") or []
    if lookup.get("kind") == "person" and len(records) == 1:
        name = records[0]["name"]
        return [f"Where is {name}'s cabin?", f"What are {name}'s qualifications?", f"What is {name}'s email?"]
    if records:
        first = records[0]["name"]
        return [f"What is {first}'s email and cabin?"]
    return []


HEADING = re.compile(r"\b([A-Z][a-z]+(?:[ -](?:of|and|for|the|in|to)?\s?[A-Z][a-z]+){1,3})\b")
NOT_TOPICS = {"manipal institute of technology", "manipal academy of higher education", "mit manipal", "constituent unit"}
BOILERPLATE_SHARE = 0.02  # a heading on more than 2% of all passages is a letterhead or table header


@lru_cache
def _passages_lower() -> tuple[str, ...]:
    from app.rag.store import get_store

    return tuple(str(c.get("text", "")).lower() for c in get_store().chunks)


@lru_cache(maxsize=4096)
def _boilerplate(phrase: str) -> bool:
    passages = _passages_lower()
    needle, limit, seen = phrase.lower(), BOILERPLATE_SHARE * len(passages), 0
    for text in passages:
        if needle in text:
            seen += 1
            if seen > limit:
                return True
    return False


def _document_suggestions(question: str, evidence: dict) -> list[str]:
    """'What does <document> say about <topic>?' for headings in the cited passage."""
    title = _title(str(evidence.get("source_file") or evidence.get("source") or ""))
    if not title:
        return []
    asked = set(index_tokens(question))
    topics, seen = [], set()
    for phrase in HEADING.findall(evidence.get("text", "")):
        key = " ".join(index_tokens(phrase))
        tokens = set(key.split())
        if (not key or key in seen or phrase.lower() in NOT_TOPICS or tokens <= asked
                or tokens & set(index_tokens(title)) == tokens or _boilerplate(phrase)):
            continue
        seen.add(key)
        topics.append(phrase)
        if len(topics) == 2:
            break
    return [f"What does the {title} say about {topic.lower()}?" for topic in topics]


def _answerable(question: str, evidence: list[dict]) -> bool:
    terms = query_terms(question)
    joined = {"text": " ".join(f"{e.get('source_file', '')} {e.get('source', '')} {e.get('text', '')}" for e in evidence)}
    return bool(terms) and relevance(terms, joined) >= MIN_COVERAGE


def suggest(question: str, evidence: list[dict], model_followups: list[str], faculty_lookup: dict | None) -> list[str]:
    """Up to three follow-ups the same evidence can answer."""
    if not evidence:
        return []
    candidates = list(model_followups)
    if faculty_lookup:
        candidates += _faculty_suggestions(faculty_lookup)
    for item in evidence:
        method = item.get("retrieval_method")
        if method == "structured_calendar":
            candidates += _calendar_suggestions(item)
        elif method == "structured_clubs" and item.get("kind") == "club":
            candidates += _club_suggestions(item)
    if not faculty_lookup and evidence[0].get("retrieval_method", "").startswith(("bm25", "dense", "colvision", "source_scan")):
        candidates += _document_suggestions(question, evidence[0])

    asked = " ".join(index_tokens(question))
    out, seen = [], set()
    for candidate in candidates:
        candidate = " ".join(candidate.split())
        key = " ".join(index_tokens(candidate))
        if not key or key == asked or key in seen or len(candidate) > 140:
            continue
        if not _answerable(candidate, evidence):
            continue
        seen.add(key)
        out.append(candidate if candidate.endswith("?") else candidate + "?")
        if len(out) == MAX_FOLLOWUPS:
            break
    return out
