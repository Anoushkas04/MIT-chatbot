import csv
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter

from app.config import DOCS_DIR

router = APIRouter(prefix="/api/faculty", tags=["4. Faculty & Cabin Directory"])


@lru_cache
def _load_faculty() -> list[dict]:
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


@router.get("", summary="Search the source-backed faculty and cabin directory")
def get_faculty(query: Optional[str] = None, dept: Optional[str] = None, page: int = 1, page_size: int = 25):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    faculty = _load_faculty()
    if dept and dept.lower() != "all":
        faculty = [item for item in faculty if dept.lower() in item["dept"].lower()]
    if query and query.strip():
        terms = [term for term in query.lower().split() if term]
        faculty = [
            item for item in faculty
            if all(term in " ".join(str(value or "") for value in item.values()).lower() for term in terms)
        ]

    total = len(faculty)
    offset = (page - 1) * page_size
    return {
        "count": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
        "data": faculty[offset:offset + page_size],
    }
