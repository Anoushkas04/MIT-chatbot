"""Rule-based entity extraction from a question.

Pulls out the things the documents are organised by (course codes, semesters, years,
months, departments) and what kind of thing is being asked about. Retrieval uses the
entities as ranking signals and to override the profile's department for this question;
the structured lookups use the intents to decide whether they apply at all.
"""
import re
from dataclasses import dataclass, field

from app.rag.metadata import normalize_department

COURSE_CODE = re.compile(r"\b([A-Z]{2,4})\s?-?(\d{4})\b")
YEAR = re.compile(r"\b(20[12]\d)(?:\s?[-–/]\s?(\d{2,4}))?\b")
MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7,
    "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
MONTHS.update({name[:3]: number for name, number in list(MONTHS.items()) if name != "may"})
ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8}
ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8}
SEMESTER = re.compile(
    r"\b(?:(\d)(?:st|nd|rd|th)?|(first|second|third|fourth|fifth|sixth|seventh|eighth)|(viii|vii|vi|iv|v|iii|ii|i))"
    r"\s*(?:-|\s)?\s*(?:sem|semester)\b|\b(?:sem|semester)\s*-?\s*(\d|viii|vii|vi|iv|v|iii|ii|i)\b",
    re.IGNORECASE,
)
# Department names and codes as students write them (metadata.normalize_department maps them)
DEPARTMENT_WORDS = re.compile(
    r"\b(cse|aiml|ai\s?&\s?ml|ai\s?ml|cce|it|dse|ece|eee|eie|ice|mech|mechx|mechatronics|aero|aeronautical|auto|automobile|"
    r"civil|chemical|biotech|biotechnology|biomedical|bme|industrial|mnc|computer science|information technology|"
    r"electronics and communication|electrical|mechanical|data science)\b",
    re.IGNORECASE,
)

INTENT_WORDS = {
    "curriculum": {"subject", "subjects", "syllabus", "curriculum", "course", "courses", "credit", "credits",
                   "elective", "electives", "semester-wise", "papers", "lab", "labs"},
    "date": {"when", "date", "dates", "deadline", "schedule", "calendar", "holiday", "holidays", "vacation"},
    "person": {"professor", "prof", "dr", "faculty", "teacher", "teachers", "lecturer", "lecturers", "hod", "cabin", "dean"},
    "club": {"club", "clubs", "society", "societies", "chapter"},
    "fee": {"fee", "fees", "tuition", "payment", "pay", "hostel fee"},
    "cutoff": {"cutoff", "cutoffs", "cut-off", "rank", "ranks", "counselling", "counseling"},
}


@dataclass
class Entities:
    course_codes: list[str] = field(default_factory=list)
    semesters: list[int] = field(default_factory=list)
    semester_parity: str | None = None  # "odd" / "even"
    years: list[int] = field(default_factory=list)
    academic_year: str | None = None  # "2026-2027"
    months: list[int] = field(default_factory=list)
    department_code: str | None = None
    department: str | None = None
    intents: set[str] = field(default_factory=set)


def extract(question: str) -> Entities:
    text = question or ""
    lowered = text.lower()
    words = set(re.findall(r"[a-z][a-z-]*", lowered))
    ent = Entities()

    # "CES 2203" is a course code; "CSE 2026" is a department and a year
    ent.course_codes = [f"{a} {b}" for a, b in COURSE_CODE.findall(text) if not 2015 <= int(b) <= 2030]

    for m in SEMESTER.finditer(text):
        digit, ordinal, roman, after = m.groups()
        value = digit or (ORDINALS.get(ordinal.lower()) if ordinal else None) or (ROMAN.get(roman.lower()) if roman else None)
        if after:
            value = int(after) if after.isdigit() else ROMAN.get(after.lower())
        if value and 1 <= int(value) <= 8 and int(value) not in ent.semesters:
            ent.semesters.append(int(value))
    if re.search(r"\beven\s+sem", lowered):
        ent.semester_parity = "even"
    elif re.search(r"\bodd\s+sem", lowered):
        ent.semester_parity = "odd"

    for start, end in YEAR.findall(text):
        ent.years.append(int(start))
        if end:
            end_year = int(end) if len(end) == 4 else int(start[:2] + end)
            if end_year == int(start) + 1:
                ent.academic_year = f"{start}-{end_year}"
                ent.years.append(end_year)

    ent.months = sorted({n for w in words for name, n in MONTHS.items() if w == name})

    match = DEPARTMENT_WORDS.search(text)
    if match:
        ent.department_code, ent.department = normalize_department(match.group(0))

    for intent, cues in INTENT_WORDS.items():
        if words & cues or any(" " in c and c in lowered for c in cues):
            ent.intents.add(intent)
    if ent.course_codes or ent.semesters:
        ent.intents.add("curriculum")
    if ent.months:
        ent.intents.add("date")
    return ent
