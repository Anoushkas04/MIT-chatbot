from typing import Optional
from fastapi import APIRouter
from app.database import SessionLocal
from app import models

router = APIRouter(prefix="/api/academic", tags=["3. Academic Information & Calendar"])


@router.get("/timeline", summary="Fetch canonical event timeline with real-time countdown metrics")
def get_timeline(role: Optional[str] = "student", department: Optional[str] = None, academic_year: Optional[str] = None):
    from app.calendar_engine import get_canonical_timeline
    events = get_canonical_timeline(role=role or "student", department=department, academic_year=academic_year)
    return {
        "count": len(events),
        "events": events
    }


@router.get("/calendar", summary="Fetch official academic calendar milestones")
def get_calendar(role: Optional[str] = "student", department: Optional[str] = None, academic_year: Optional[str] = None):
    from app.calendar_engine import get_canonical_timeline
    events = get_canonical_timeline(role=role or "student", department=department, academic_year=academic_year)
    key_dates = [
        {"event": e["title"], "date": e["formatted_date"], "status": e["status"], "category": e["category"], "source": e["source"]}
        for e in events
    ]
    return {
        "academic_year": "2025–26 / 2026–27",
        "key_dates": key_dates,
    }


@router.get("/cutoffs", summary="Query MET entrance counseling cutoff ranks")
def get_cutoffs(course: str = "B.Tech", round_num: Optional[int] = 1, max_rank: Optional[int] = None):
    cutoffs = [
        {"program": "Computer Science & Engineering (CSE)", "round1": 1620, "round2": 1845, "round3": 1950, "category": "General", "degree": "B.Tech"},
        {"program": "Computer Science & Financial Tech", "round1": 2450, "round2": 2810, "round3": 2980, "category": "General", "degree": "B.Tech"},
        {"program": "AI & Machine Learning (AIML)", "round1": 2110, "round2": 2390, "round3": 2510, "category": "General", "degree": "B.Tech"},
        {"program": "Information Technology (IT)", "round1": 3150, "round2": 3520, "round3": 3710, "category": "General", "degree": "B.Tech"},
        {"program": "Electronics & Communication (ECE)", "round1": 5120, "round2": 5890, "round3": 6240, "category": "General", "degree": "B.Tech"},
        {"program": "Data Science & Engineering", "round1": 3890, "round2": 4350, "round3": 4620, "category": "General", "degree": "B.Tech"},
        {"program": "Electrical & Electronics (EEE)", "round1": 9210, "round2": 10450, "round3": 11200, "category": "General", "degree": "B.Tech"},
        {"program": "Aeronautical Engineering", "round1": 12400, "round2": 14200, "round3": 15100, "category": "General", "degree": "B.Tech"},
        {"program": "Mechanical Engineering", "round1": 18500, "round2": 21300, "round3": 22800, "category": "General", "degree": "B.Tech"},
        {"program": "M.Tech Computer Science & Engg", "round1": 140, "round2": 185, "round3": 210, "category": "General", "degree": "M.Tech"},
        {"program": "M.Pharm Pharmaceutics", "round1": 85, "round2": 115, "round3": 130, "category": "General", "degree": "M.Pharm"},
    ]
    filtered = [c for c in cutoffs if c["degree"].lower() == course.lower()]
    if max_rank:
        field = f"round{round_num}" if round_num in [1, 2, 3] else "round1"
        filtered = [c for c in filtered if c.get(field, 999999) >= max_rank]
    return {"course": course, "count": len(filtered), "cutoffs": filtered}
