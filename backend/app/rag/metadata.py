import re
from pathlib import Path


DEPARTMENT_PATTERNS = (
    ("CSFT", "Computer Science and Financial Technology", (r"\bcsft\b", r"financial technology")),
    ("CSE", "Computer Science and Engineering", (r"\bcse\b", r"\bcs\b", r"computer science", r"school of computer engineering")),
    ("ECE", "Electronics and Communication Engineering", (r"\bece\b", r"electronics and communication")),
    ("EEE", "Electrical and Electronics Engineering", (r"\beee\b", r"electrical and electronics")),
    ("MECHX", "Mechatronics Engineering", (r"\bmech\s*x\b", r"mechatronics")),
    ("ME", "Mechanical Engineering", (r"\bmech\b", r"mechanical engineering")),
    ("AERO", "Aeronautical Engineering", (r"\baero\b", r"aeronautical")),
    ("AUTO", "Automobile Engineering", (r"\bautomobile\b",)),
    ("CIVIL", "Civil Engineering", (r"\bcivil\b",)),
    ("CHE", "Chemical Engineering", (r"\bchemical\b",)),
    ("BT", "Biotechnology", (r"\bbiotech\b", r"biotechnology")),
    ("BME", "Biomedical Engineering", (r"\bbiomedical\b",)),
    ("IE", "Industrial Engineering", (r"\bindustrial\b",)),
    ("MNC", "Mathematics and Computing", (r"\bmnc\b", r"math(?:ematics)? and computing")),
)


def infer_document_metadata(source: str, text: str = "") -> dict:
    filename = Path(source).name
    filename_haystack = _normalized(Path(filename).stem)
    text_haystack = _normalized(text[:800])
    haystack = f"{filename_haystack} {text_haystack}".strip()
    department_code = None
    department = None
    for candidate in (filename_haystack, text_haystack):
        for code, name, patterns in DEPARTMENT_PATTERNS:
            if any(re.search(pattern, candidate, flags=re.IGNORECASE) for pattern in patterns):
                department_code = code
                department = name
                break
        if department_code:
            break

    lowered = haystack.lower()
    if re.search(r"\bm\s*\.?tech\b|\bmtech\b", lowered):
        programme = "M.Tech"
    elif re.search(r"\bb\s*\.?tech\b|\bbtech\b", lowered):
        programme = "B.Tech"
    elif "mca" in lowered:
        programme = "MCA"
    elif "m.sc" in lowered or "msc" in lowered:
        programme = "M.Sc"
    else:
        programme = None

    academic_year = _academic_year(filename)
    document_type = _document_type(filename, lowered)
    semester = _semester(lowered)
    return {
        "department_code": department_code,
        "department": department,
        "programme": programme,
        "academic_year": academic_year,
        "semester": semester,
        "document_type": document_type,
    }


def normalize_department(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    normalized = _normalized(value)
    for code, name, patterns in DEPARTMENT_PATTERNS:
        if normalized.upper() == code or any(
            re.search(pattern, normalized, flags=re.IGNORECASE)
            for pattern in patterns
        ):
            return code, name
    return None, value.strip()


def _normalized(value: str) -> str:
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    value = re.sub(r"[_\-]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _academic_year(filename: str) -> str | None:
    match = re.search(r"(20\d{2})\s*[-–_]\s*(20\d{2}|\d{2})", filename)
    if match:
        end = match.group(2)
        if len(end) == 2:
            end = f"{match.group(1)[:2]}{end}"
        return f"{match.group(1)}-{end}"
    short_match = re.search(r"(?<!\d)(2\d)\s*[-–_]\s*(2\d)(?!\d)", filename)
    if short_match:
        return f"20{short_match.group(1)}-20{short_match.group(2)}"
    years = re.findall(r"20\d{2}", filename)
    return years[0] if years else None


def _document_type(filename: str, lowered: str) -> str:
    name = filename.lower()
    if "calendar" in name:
        return "academic_calendar"
    if "first year" in name and ("b.tech" in name or "btech" in name):
        return "curriculum"
    if "faculty" in name or "cabin" in name:
        return "faculty_directory"
    if "syllabus" in name:
        return "syllabus"
    if "course plan" in name or re.search(r"(^|[_\s])(plan|cp)([_\s.]|$)", name):
        return "course_plan"
    if "cut off" in name or "cutoff" in name:
        return "cutoff_rank"
    if "regulation" in name:
        return "regulations"
    if "notice" in name or "notification" in name:
        return "notice"
    if "guideline" in name:
        return "guidelines"
    if "club" in name:
        return "clubs"
    if "fee" in lowered or "inr" in lowered:
        return "fees"
    return "document"


def _semester(lowered: str) -> str | None:
    if "odd semester" in lowered:
        return "Odd"
    if "even semester" in lowered:
        return "Even"
    match = re.search(r"\b([1-8]|i{1,3}|iv|v|vi|vii|viii)\s+(?:semester|sem)\b", lowered)
    return match.group(1).upper() if match else None
