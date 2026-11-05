import csv
import re
from collections import Counter
from functools import lru_cache

from app.config import DOCS_DIR


DEPARTMENT_ALIASES = {
    "School of Computer Engineering": (
        "school of computer engineering", "school of computing", "computing",
        "computer engineering", "computer science",
        "information technology", "data science", "artificial intelligence",
        "machine learning", "cse", "sce", "it", "dse", "aiml",
    ),
    "School of Electrical Engineering": (
        "school of electrical engineering", "electrical engineering", "electronics engineering",
        "electronics and communication", "electronics & communication", "communication engineering",
        "biomedical engineering", "instrumentation", "electrical", "electronics",
        "ece", "eee", "bme", "ice",
    ),
    "School of Mechanical Engineering": (
        "school of mechanical engineering", "mechanical engineering", "mechatronics engineering",
        "automobile engineering", "aeronautical engineering", "industrial engineering",
        "mechanical", "mechatronics", "automobile", "aeronautical", "aerospace",
        "mech", "mechx", "auto", "aero", "ie",
    ),
    "School of Civil & Chemical Engineering": (
        "school of civil and chemical engineering", "school of civil & chemical engineering",
        "civil engineering", "chemical engineering", "biotechnology", "civil", "chemical",
        "civil and chemical", "civil & chemical", "biotech", "bt",
    ),
    "School of Basic Sciences, Humanities & Management": (
        "school of basic sciences humanities and management",
        "school of basic sciences, humanities & management", "basic sciences",
        "humanities and management", "humanities", "management", "mathematics", "maths", "math",
        "physics", "chemistry", "bs hm", "bshm",
    ),
}

HONORIFIC_TOKENS = {
    "dr", "doctor", "prof", "professor", "mr", "mrs", "ms", "miss",
}
PERSON_QUERY_STOPWORDS = HONORIFIC_TOKENS | {
    "about", "and", "cabin", "can", "contact", "details", "does", "email", "faculty",
    "for", "give", "her", "his", "information", "is", "know", "me", "member", "of", "office",
    "please", "room", "tell", "the", "what", "where", "which", "who", "you", "s",
    "their",
}
LIST_SIGNALS = {"list", "show", "names", "members", "professor", "professors", "faculty", "teachers", "lecturers"}


def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.lower().replace("&", " and "))


MERGED_FACULTY_FILE = "merged_faculty.csv"
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Roles some rows carry in the name column, e.g. "Dr. X Adjunct Faculty"
NAME_ROLE_RE = re.compile(r"\s+((?:International\s+)?Adjunct\b.*|International Faculty\b.*)$", re.IGNORECASE)
QUALIFICATION_PREFIX_RE = re.compile(r"^qualifications?\s*:\s*", re.IGNORECASE)


def _clean(value: str | None) -> str:
    return " ".join((value or "").split())


def _take_email(text: str) -> tuple[str, str]:
    """Split an email address written into another column out of it."""
    match = EMAIL_RE.search(text)
    if not match:
        return text, ""
    return _clean(text[: match.start()] + text[match.end():]), match.group(0).lower()


def _load_merged(path) -> list[dict]:
    """The master faculty CSV (official directory merged with the SCE cabin list).

    Some rows have the role or an email typed into the name or designation column; those are
    moved to their own fields. Nothing missing is filled in.
    """
    records: dict[str, dict] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            name, name_email = _take_email(_clean(row.get("professor name")))
            designation, designation_email = _take_email(_clean(row.get("title/designation")))
            role = NAME_ROLE_RE.search(name)
            if role:
                name = name[: role.start()].strip()
                designation = designation or role.group(1).rstrip(" .")
            bare_name = re.sub(r"^(?:(?:Dr|Prof|Mr|Mrs|Ms|Cmde)\.?\s*)+", "", name)
            if bare_name and designation.endswith(bare_name):  # "Assistant Professor ... <their own name>"
                designation = designation[: -len(bare_name)].strip()
            designation = re.sub(r"\S+@\S+(?:\s+edu)?$", "", designation).strip()  # a broken address
            email = _clean(row.get("mail id")).lower() or name_email or designation_email
            if email.startswith("noreply@"):  # a placeholder shared by several people, not a contact
                email = ""
            dept = _clean(row.get("department"))
            if not name:
                continue
            key = email or f"{name.lower()}|{dept.lower()}"
            if key in records:
                continue
            records[key] = {
                "id": f"faculty-{len(records) + 1}",
                "name": name,
                "dept": dept,
                "designation": designation,
                "cabin": _clean(row.get("cabin no.")) or None,
                "email": email,
                "qualification": QUALIFICATION_PREFIX_RE.sub("", _clean(row.get("qualification"))),
                "source": path.name,
            }
    return sorted(records.values(), key=lambda faculty: faculty["name"].lower())


@lru_cache
def load_faculty() -> list[dict]:
    """The master faculty directory (merged_faculty.csv), or nothing if it isn't there."""
    path = DOCS_DIR / MERGED_FACULTY_FILE
    return _load_merged(path) if path.is_file() else []


def detect_department(query: str) -> str | None:
    normalized = " ".join(_tokens(query))
    candidates: list[tuple[int, str]] = []
    for department, aliases in DEPARTMENT_ALIASES.items():
        for alias in aliases:
            normalized_alias = " ".join(_tokens(alias))
            if re.search(rf"\b{re.escape(normalized_alias)}\b", normalized):
                candidates.append((len(normalized_alias), department))
    return max(candidates)[1] if candidates else None


def _person_matches(query: str) -> list[dict]:
    query_tokens = [
        token for token in _tokens(query)
        if token not in PERSON_QUERY_STOPWORDS and len(token) > 1
    ]
    if not query_tokens:
        return []
    query_set = set(query_tokens)
    ranked = []
    for record in load_faculty():
        name_tokens = {
            token for token in _tokens(record["name"])
            if token not in HONORIFIC_TOKENS and len(token) > 1
        }
        overlap = query_set.intersection(name_tokens)
        if not overlap:
            continue
        contains_all = query_set.issubset(name_tokens)
        if len(query_set) > 1 and not contains_all:
            continue
        ranked.append((contains_all, len(overlap), -len(name_tokens), record))
    ranked.sort(key=lambda item: item[:3], reverse=True)
    matches = [item[3] for item in ranked]
    if len(query_set) == 1 and len(matches) != 1:
        return matches[:8]
    return matches[:4]


def _record_text(record: dict) -> str:
    fields = [
        f"Name: {record['name']}",
        f"Department: {record['dept']}",
        f"Designation: {record['designation'] or 'Not specified'}",
        f"Email: {record['email'] or 'Not listed'}",
    ]
    if record.get("cabin"):
        fields.append(f"Cabin: {record['cabin']}")
    if record.get("qualification"):
        fields.append(f"Qualification: {record['qualification']}")
    return ". ".join(fields) + "."


def _evidence(text: str, source: str) -> dict:
    return {
        "id": f"faculty-structured-{abs(hash(text))}",
        "document_id": "faculty-directory",
        "source": source,
        "source_file": source,
        "source_type": "official",
        "document_type": "faculty_directory",
        "text": text,
        "score": 1.0,
        "retrieval_method": "structured_faculty_directory",
    }


def _named_people(query: str) -> list[dict]:
    """Faculty whose first and last name (two or more name words) both appear in the query."""
    query_set = {t for t in _tokens(query) if t not in PERSON_QUERY_STOPWORDS and len(t) > 1}
    found = []
    for record in load_faculty():
        name_tokens = {t for t in _tokens(record["name"]) if t not in HONORIFIC_TOKENS and len(t) > 1}
        if len(name_tokens & query_set) >= 2:
            found.append((len(name_tokens & query_set), record))
    best = max((n for n, _ in found), default=0)
    return [r for n, r in found if n == best]


def lookup_faculty(query: str) -> dict | None:
    """Return deterministic faculty evidence and an answer for supported directory queries."""
    query_tokens = set(_tokens(query))
    department = detect_department(query)
    # "Professor Sanjay Singh in the SCE faculty rooms" is about one person, not the SCE list
    is_directory_list = bool(department and query_tokens.intersection(LIST_SIGNALS)) and not _named_people(query)
    if is_directory_list:
        records = [record for record in load_faculty() if record["dept"] == department]
        if not records:
            return None
        lines = [f"{index}. {record['name']} — {record['designation'] or 'Designation not specified'}" for index, record in enumerate(records, start=1)]
        counts = ", ".join(
            f"{designation or 'Unspecified'}: {count}"
            for designation, count in Counter(record["designation"] for record in records).most_common()
        )
        evidence_text = (
            f"Official faculty directory for {department}. Total faculty records: {len(records)}. "
            f"Designation counts: {counts}. Faculty list:\n" + "\n".join(lines)
        )
        answer = (
            f"{department} has {len(records)} faculty records (all academic designations):\n\n"
            + "\n".join(lines)
            + "\n\nSource: official faculty directory [E1]"
        )
        return {
            "answer": answer,
            "evidence": _evidence(evidence_text, "MIT faculty directory (CSV)"),
            "records": records,
            "kind": "department_list",
        }

    person_signals = {"about", "cabin", "contact", "email", "professor", "faculty", "where", "who"}
    if not query_tokens.intersection(person_signals):
        return None
    records = _named_people(query) or _person_matches(query)
    if not records:
        return None
    evidence_text = "\n".join(_record_text(record) for record in records)
    if len(records) == 1:
        record = records[0]
        details = [
            f"{record['name']} — {record['designation'] or 'designation not specified'}",
            record["dept"],
            f"Email: {record['email'] or 'Not listed'}",
        ]
        if record.get("cabin"):
            details.append(f"Cabin: {record['cabin']}")
        else:
            details.append("Cabin: Not listed in the faculty directory")
        if record.get("qualification"):
            details.append(f"Qualification: {record['qualification']}")
        answer = "\n".join(details) + "\n\nSource: official faculty directory [E1]"
    else:
        names = "\n".join(
            f"- {record['name']} — {record['designation'] or 'designation not specified'}, {record['dept']}"
            for record in records
        )
        answer = (
            "That name is ambiguous in the faculty directory. Please use the full name or department:\n\n"
            f"{names}\n\nSource: official faculty directory [E1]"
        )
    return {
        "answer": answer,
        "evidence": _evidence(evidence_text, records[0]["source"]),
        "records": records,
        "kind": "person",
    }
