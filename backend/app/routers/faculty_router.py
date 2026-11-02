from typing import Optional

from fastapi import APIRouter

from app.faculty_directory import load_faculty

router = APIRouter(prefix="/api/faculty", tags=["4. Faculty & Cabin Directory"])


_load_faculty = load_faculty


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
