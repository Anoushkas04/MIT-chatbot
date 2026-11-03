from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from app.database import SessionLocal
from app import models
from app.routers.auth_router import get_current_user

router = APIRouter(prefix="/api/users", tags=["6. Student Network & Safety"])

REPORT_REASONS = ["Harassment", "Inappropriate content", "Spam or scam", "Other"]


class UserReportRequest(BaseModel):
    reported_user_id: Optional[str] = None  # None for people who don't have a backend account
    reported_name: str
    reason: str
    details: Optional[str] = ""
    recent_messages: List[str] = []


@router.get("/search", summary="Search registered students by name, department or interests")
def search_users(q: str = Query(..., min_length=2, max_length=80), current_user: models.User = Depends(get_current_user)):
    term = f"%{q.strip()}%"
    db = SessionLocal()
    try:
        users = (
            db.query(models.User)
            .filter(
                models.User.id != current_user.id,
                models.User.status == "active",
                models.User.is_suspended.is_(False),
                or_(
                    models.User.name.ilike(term),
                    models.User.department.ilike(term),
                    models.User.interests.ilike(term),
                ),
            )
            .order_by(models.User.name)
            .limit(20)
            .all()
        )
        # Public profile fields only: never email, learner ID, registration number or strike data.
        return {
            "results": [
                {
                    "id": u.id,
                    "name": u.name,
                    "department": u.department or "",
                    "semester": u.semester or "",
                    "academic_year": u.academic_year or "",
                    "interests": [i.strip() for i in (u.interests or "").split(",") if i.strip()],
                }
                for u in users
            ]
        }
    finally:
        db.close()


@router.post("/report", summary="Report a student from a private chat for admin review")
def report_user(req: UserReportRequest, current_user: models.User = Depends(get_current_user)):
    if req.reason not in REPORT_REASONS:
        raise HTTPException(status_code=400, detail=f"Reason must be one of: {', '.join(REPORT_REASONS)}.")
    if req.reported_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You can't report yourself.")

    db = SessionLocal()
    try:
        reported_id = None
        if req.reported_user_id:
            reported = db.query(models.User).filter(models.User.id == req.reported_user_id).first()
            if not reported:
                raise HTTPException(status_code=404, detail="Reported user not found.")
            reported_id = reported.id

        lines = [f"Reported by {current_user.name} ({current_user.id})"]
        if req.details and req.details.strip():
            lines.append(f"Details: {req.details.strip()[:1000]}")
        if req.recent_messages:
            lines.append("Recent messages from them:")
            lines.extend(f"- {m[:300]}" for m in req.recent_messages[-5:])

        violation = models.CommunityViolation(
            user_id=reported_id,
            user_name=req.reported_name.strip()[:120],
            violation_category=req.reason,
            prohibited_content_snippet="\n".join(lines),
            moderation_result="User Report",
            # A report is a claim awaiting review, not a confirmed strike.
            strike_number=0,
            admin_review_status="Pending Admin Review",
        )
        db.add(violation)
        db.commit()
        return {"status": "success", "message": "Report submitted for admin review.", "report_id": violation.id}
    finally:
        db.close()
