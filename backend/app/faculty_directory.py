import csv
import re
from collections import Counter
from functools import lru_cache

from app.config import DOCS_DIR


DEPARTMENT_ALIASES = {
    "School of Computer Engineering": (
        "school of computer engineering", "computer engineering", "computer science",
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
        "civil and chemical", "civil & chemical", "bt",
    ),
    "School of Basic Sciences, Humanities & Management": (
        "school of basic sciences humanities and management",
        "school of basic sciences, humanities & management", "basic sciences",
        "humanities and management", "humanities", "management", "mathematics",
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
LIST_SIGNALS = {"list", "show", "names", "members", "professor", "professors", "faculty", "teachers"}


def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.lower().replace("&", " and "))


@lru_cache
def load_faculty() -> list[dict]:
    """Load and de-duplicate the two source-backed faculty CSV directories."""
    by_email: dict[str, dict] = {}
    general_path = DOCS_DIR / "mit_manipal_faculty.csv"
    if general_path.is_file():
        with general_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                email = (row.get("Mail ID") or "").strip().lower()
                if not email:
                    continue
                by_email[email] = {
                    "id": f"faculty-{len(by_email) + 1}",
                    "name": (row.get("Professor Name") or "").strip(),
                    "dept": (row.get("Department") or "").strip(),
                    "designation": (row.get("Title") or "").strip(),
                    "cabin": None,
                    "email": email,
                    "qualification": (row.get("Qualification") or "").strip(),
                    "source": general_path.name,
                }

    cabins_path = DOCS_DIR / "manipal_sce_faculty_cabins.csv"
    if cabins_path.is_file():
        with cabins_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                email = (row.get("email") or "").strip().lower()
                if not email:
                    continue
                existing = by_email.get(email, {})
                by_email[email] = {
                    "id": row.get("id") or existing.get("id") or f"faculty-{len(by_email) + 1}",
                    "name": (row.get("name") or existing.get("name") or "").strip(),
                    "dept": existing.get("dept") or "School of Computer Engineering",
                    "designation": (row.get("designation") or existing.get("designation") or "").strip(),
                    "cabin": (row.get("cabin_no") or "").strip() or None,
                    "email": email,
                    "qualification": existing.get("qualification") or "",
                    "source": cabins_path.name,
                }
    return sorted(by_email.values(), key=lambda faculty: faculty["name"].lower())


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
        f"Email: {record['email']}",
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


def lookup_faculty(query: str) -> dict | None:
    """Return deterministic faculty evidence and an answer for supported directory queries."""
    query_tokens = set(_tokens(query))
    department = detect_department(query)
    is_directory_list = bool(department and query_tokens.intersection(LIST_SIGNALS))
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
    records = _person_matches(query)
    if not records:
        return None
    evidence_text = "\n".join(_record_text(record) for record in records)
    if len(records) == 1:
        record = records[0]
        details = [
            f"{record['name']} — {record['designation'] or 'designation not specified'}",
            record["dept"],
            f"Email: {record['email']}",
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
