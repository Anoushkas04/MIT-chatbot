"""Source-backed campus directories for the Utilities pages.

Faculty come from the official CSVs in DOCS_DIR, merged by institutional email
(app/faculty_directory.load_faculty). Fields a source doesn't give stay empty;
nothing is guessed.
"""
from fastapi import APIRouter, Depends

from app import models
from app.faculty_directory import load_faculty
from app.routers.auth_router import get_current_user

router = APIRouter(prefix="/api/directory", tags=["10. Global Intelligent Search"])


@router.get("/faculty", summary="Faculty directory: designation, department, qualification, email and cabin")
def faculty(me: models.User = Depends(get_current_user)):
    return {
        "faculty": [
            {
                "id": f["id"],
                "name": f["name"],
                "designation": f["designation"],
                "department": f["dept"],
                "qualification": f["qualification"].removeprefix("Qualification:").strip(),
                "email": f["email"],
                "cabin": f["cabin"],
            }
            for f in load_faculty()
        ],
        "sources": ["mit_manipal_faculty.csv", "manipal_sce_faculty_cabins.csv"],
    }
