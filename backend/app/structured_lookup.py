"""Structured evidence for questions that free-text retrieval answers poorly.

Dates come from the 2026-27 academic calendar (one dated line per event) and clubs from
the official club records, so "when are the holidays in November" or "clubs for robotics"
get the exact entries however they're phrased. Each matching calendar section or club is
its own evidence record, so it's cited and linked separately. Like faculty_directory,
nothing is inferred beyond the source lines.
"""
import datetime
import json
import re
from functools import lru_cache

from app.config import BACKEND_DIR, DOCS_DIR
from app.rag.text_norm import expand_query, index_tokens

CALENDAR_FILE = "MIT_Manipal_Academic_Calendar_2026-27.md"
CALENDAR_PDF = "Academic Calendar 26-27 (1).pdf"  # the official document the .md transcribes
CLUBS_FILE = BACKEND_DIR / "data" / "clubs.jsonl"
CLUBS_PDF = "clubs.pdf"

MONTHS = {
    m: i for i, m in enumerate(
        ["january", "february", "march", "april", "may", "june", "july",
         "august", "september", "october", "november", "december"], start=1)
}
MONTHS.update({m[:3]: i for m, i in list(MONTHS.items())})
# Words that make a question about dates. Generic ones ("end", "start", "results", "last") are
# not enough on their own: "attendance needed to write the end-semester exam" isn't a date question.
DATE_SIGNALS = {
    "when", "date", "dates", "deadline", "schedule", "calendar", "holiday", "holidays",
    "vacation", "upcoming", "fest", "revels", "techtatva", "utsav",
}
# Too common in calendar lines to tell entries apart
CALENDAR_GENERIC = {
    "semester", "sem", "date", "day", "start", "end", "last", "course", "tech", "b", "mit",
    # words about the calendar itself, not an event in it ("what date is Christmas marked on the calendar")
    "academic", "calendar", "mark", "list", "show", "year", "manipal",
}
CLUB_GENERIC = {
    "club", "clubs", "society", "chapter", "manipal", "mit", "student", "students", "official", "join",
    "technical", "non", "nontechnical", "cultural", "all", "available", "name", "every",
}
# Club pages in the source that belong to a different club
WRONG_CLUB_PAGES = {"180-degree-consulting", "the-psych-club"}
# Student phrasing -> the wording calendar entries use, worth more than a single shared word
CALENDAR_PHRASES = {
    "end semester": ("end sem", "endsem", "end-sem", "end semester", "final exam", "finals"),
    "mid-term": ("mid sem", "midsem", "mid-sem", "midterm", "mid term", "mid-term"),
    "makeup": ("makeup", "make up", "make-up", "supplementary"),
    "re-regist": ("re-registration", "reregistration", "re-register", "re register"),
    "re-test": ("retest", "re-test", "re test"),
    "branch change": ("branch change", "change branch", "change my branch"),
    "classes start": ("classes start", "class start", "college start", "reopen", "semester start"),
    "instructional day": ("last working day", "last day of class", "last instructional", "classes end"),
    "result": ("result", "results"),
}

_LINE = re.compile(
    r"^- (?P<start>\d{4}-\d{2}-\d{2})(?: \(\w+\))?(?: to (?P<end>\d{4}-\d{2}-\d{2})(?: \(\w+\))?)? — (?P<title>.+)$"
)
_SUMMARY = re.compile(r"^- (?P<title>[^:]+): (?P<when>.*\d{4}-\d{2}-\d{2}.*)$")


def _today() -> str:
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).date().isoformat()


@lru_cache
def calendar_entries() -> list[dict]:
    path = DOCS_DIR / CALENDAR_FILE
    if not path.is_file():
        return []
    entries, section = [], ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("#"):
            section = line.lstrip("# ").strip()
            continue
        if section.startswith("General Notes"):
            continue
        match = _LINE.match(line)
        if match:
            entries.append({
                "start": match["start"], "end": match["end"] or match["start"],
                "title": match["title"], "section": section, "line": line[2:],
            })
            continue
        match = _SUMMARY.match(line)
        if match and section.endswith(")"):  # Key Dates Summary semesters
            dates = re.findall(r"\d{4}-\d{2}-\d{2}", match["when"])
            entries.append({
                "start": dates[0], "end": dates[-1], "title": match["title"],
                "section": f"Key dates, {section}", "line": line[2:],
            })
    return entries


def _requested_months(tokens: list[str]) -> set[int]:
    return {MONTHS[t] for t in tokens if t in MONTHS}


def calendar_evidence(query: str, limit: int = 12) -> list[dict]:
    raw = re.findall(r"[a-z0-9]+", query.lower())
    months = _requested_months(raw)
    if not (DATE_SIGNALS.intersection(raw) or months):
        return []
    wanted = {t for t in index_tokens(expand_query(query)) if not t.isdigit()} - CALENDAR_GENERIC - set(MONTHS)
    wants_holidays = bool({"holiday", "vacation", "leave", "break"}.intersection(index_tokens(query)))
    lowered = " ".join(raw)
    phrases = [target for target, said in CALENDAR_PHRASES.items() if any(s in query.lower() or s in lowered for s in said)]
    today = _today()
    scored = []
    for e in calendar_entries():
        if months and not any(
            int(d[5:7]) in months for d in (e["start"], e["end"])
        ):
            continue
        is_holiday = e["section"].startswith("Holidays") or "holiday" in e["title"].lower()
        overlap = len(wanted.intersection(index_tokens(e["title"])))
        if wants_holidays and is_holiday:
            overlap += 2
        overlap += 3 * sum(target in e["title"].lower() for target in phrases)
        if overlap == 0 and not (months and not wanted):
            continue
        upcoming = e["end"] >= today
        scored.append((overlap, upcoming, e))
    if not scored:
        return []
    best = max(s[0] for s in scored)
    # Keep the strongest matches; prefer what's still ahead, then by date
    chosen = [s for s in scored if s[0] >= max(1, best - 1)] if best else scored
    chosen.sort(key=lambda s: (-s[0], not s[1], s[2]["start"]))
    seen, picked = set(), []
    for _, _, e in chosen:
        key = (e["start"], e["end"], re.sub(r"\s*\((?:holiday)\)", "", e["title"].lower())[:40])
        if key in seen:
            continue
        seen.add(key)
        picked.append(e)
        if len(picked) >= limit:
            break
    picked.sort(key=lambda e: e["start"])
    lines = "\n".join(f"- {e['line']}" for e in picked)
    text = (
        f"Official MIT Manipal Academic Calendar 2026-27. Today's date is {today}. "
        f"Matching entries (YYYY-MM-DD):\n{lines}"
    )
    return [{
        "id": f"calendar-{abs(hash(lines))}",
        "document_id": "academic-calendar-2026-27",
        "source": "Academic Calendar 2026-27",
        "source_file": CALENDAR_PDF if (DOCS_DIR / CALENDAR_PDF).is_file() else CALENDAR_FILE,
        "source_type": "official",
        "kind": "calendar",
        "text": text,
        "score": 1.0,
        "retrieval_method": "structured_calendar",
    }]


def _clean_description(text: str) -> str:
    paras = []
    for p in re.split(r"\n\s*\n", text or ""):
        p = " ".join(p.split())
        if not p or p.startswith("We use cookies") or re.match(r"(?i)^(official )?(club )?(e-?mail|mail id)", p):
            continue
        paras.append(p)
    return " ".join(paras)


@lru_cache
def club_records() -> list[dict]:
    if not CLUBS_FILE.is_file():
        return []
    clubs, seen = [], set()
    for line in CLUBS_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        name = row["name"].strip()
        if name == "Our Programs" or name.lower() in seen:
            continue
        seen.add(name.lower())
        description = _clean_description(row.get("description", ""))
        clubs.append({
            "name": name.title() if name.isupper() and len(name) > 10 else name,
            "category": "Technical" if row.get("category") == "technical" else "Non-technical",
            "emails": row.get("emails") or [],
            "url": row.get("source_url"),
            "description": description,
            "tokens": set(index_tokens(f"{name} {description}")),
        })
    # One page in the source is shared by two clubs; only keep it for the club it's named after
    pages: dict = {}
    for c in clubs:
        pages.setdefault((c["url"] or "").rsplit("/", 1)[-1].lower(), []).append(c)
    for c in clubs:
        if any(wrong in (c["url"] or "") for wrong in WRONG_CLUB_PAGES):
            c["url"] = None
    for page, owners in pages.items():
        if len(owners) > 1:
            for c in owners:
                if c["name"].split()[0].lower() not in page:
                    c["url"] = None
    return clubs


def club_evidence(query: str, limit: int = 5) -> list[dict]:
    raw = set(re.findall(r"[a-z0-9]+", query.lower()))
    if not raw.intersection({"club", "clubs", "society", "societies", "chapter"}):
        return []
    clubs = club_records()
    if not clubs:
        return []
    wanted = set(index_tokens(expand_query(query))) - CLUB_GENERIC
    category = (
        "Technical" if "technical" in raw and "non" not in raw
        else "Non-technical" if raw.intersection({"cultural", "non", "nontechnical"}) else None
    )
    scored = []
    for c in clubs:
        if category and c["category"] != category:
            continue
        name_tokens = set(index_tokens(c["name"]))
        score = 3 * len(wanted.intersection(name_tokens)) + len(wanted.intersection(c["tokens"]))
        scored.append((score, c))
    matches = [c for s, c in sorted(scored, key=lambda x: -x[0]) if s > 0][:limit]
    if matches:
        return [_club_record(c) for c in matches]
    # "what clubs are there" / "list technical clubs": the full official list
    pool = [c for c in clubs if not category or c["category"] == category]
    names = "\n".join(f"- {c['name']} ({c['category']})" for c in pool)
    return [{
        "id": f"clubs-list-{category or 'all'}",
        "document_id": "mit-clubs",
        "source": "MIT Manipal official clubs list",
        "source_file": CLUBS_PDF,
        "source_type": "official",
        "kind": "document",
        "text": f"Official MIT Manipal student clubs ({len(pool)}{' ' + category if category else ''}):\n{names}",
        "score": 1.0,
        "retrieval_method": "structured_clubs",
    }]


def _club_record(c: dict) -> dict:
    contact = f" Email: {', '.join(c['emails'])}." if c["emails"] else ""
    return {
        "id": f"club-{re.sub(r'[^a-z0-9]+', '-', c['name'].lower()).strip('-')}",
        "document_id": "mit-clubs",
        "source": f"{c['name']} (official club page)",
        "source_file": CLUBS_PDF,
        "source_type": "official",
        "kind": "club",
        "url": c["url"],
        "text": f"{c['name']} — {c['category']} club at MIT Manipal.{contact} {c['description'][:900]}",
        "score": 1.0,
        "retrieval_method": "structured_clubs",
    }
