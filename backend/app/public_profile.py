"""Public student profiles: what other students see when they open someone from Network.

Clubs and student projects are stored on the user as JSON lists of {"name", "role"}.
Only the fields in public_profile() are ever shown to other students: never email,
learner ID, registration number, strikes or suspension data.
"""
import json
from typing import Any, List

from fastapi import HTTPException

from app import models
from app.moderation_engine import evaluate_community_content

MAX_ENTRIES = 15
MAX_NAME = 80
MAX_ROLE = 60


def parse_entries(raw: str | None) -> List[dict]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except ValueError:
        return []
    return [
        {"name": str(e.get("name", "")), "role": str(e.get("role", ""))}
        for e in data
        if isinstance(e, dict) and e.get("name")
    ]


def clean_entries(items: List[Any], label: str) -> List[dict]:
    """Trims, de-duplicates and validates entries from the profile editor."""
    out: List[dict] = []
    seen = set()
    for item in items:
        name = " ".join(str(getattr(item, "name", "") or "").split())
        role = " ".join(str(getattr(item, "role", "") or "").split())
        if not name or name.lower() in seen:
            continue
        if len(name) > MAX_NAME or len(role) > MAX_ROLE:
            raise HTTPException(status_code=400, detail=f"Keep {label} names under {MAX_NAME} characters and roles under {MAX_ROLE}.")
        prohibited, _, _, _ = evaluate_community_content(name, role)
        if prohibited:
            raise HTTPException(status_code=400, detail=f'"{name}" can\'t be shown on your public profile.')
        seen.add(name.lower())
        out.append({"name": name, "role": role})
    if len(out) > MAX_ENTRIES:
        raise HTTPException(status_code=400, detail=f"You can list up to {MAX_ENTRIES} {label}.")
    return out


def public_profile(user: models.User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "department": user.department or "",
        "semester": user.semester or "",
        "academic_year": user.academic_year or "",
        "interests": [i.strip() for i in (user.interests or "").split(",") if i.strip()],
        "clubs": parse_entries(user.clubs),
        "projects": parse_entries(user.projects),
    }
