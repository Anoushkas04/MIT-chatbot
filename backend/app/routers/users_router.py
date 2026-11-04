from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from app.database import SessionLocal
from app import models
from app.routers.auth_router import get_current_user
from app.public_profile import public_profile

router = APIRouter(prefix="/api/users", tags=["6. Student Network & Safety"])


class UserReportRequest(BaseModel):
    reported_user_id: Optional[str] = None  # None for people who don't have a backend account
    reported_name: str
    reason: str
    note: Optional[str] = ""
    # Deliberately no message-content field: private chats never leave the device.


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


@router.get("/{user_id}", summary="A student's public profile (details, interests, clubs and projects)")
def get_public_profile(user_id: str, current_user: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        user = (
            db.query(models.User)
            .filter(
                models.User.id == user_id,
                models.User.role != "admin",
                models.User.status == "active",
                models.User.is_suspended.is_(False),
            )
            .first()
        )
        if not user:
            raise HTTPException(status_code=404, detail="This profile isn't available.")
        return public_profile(user)
    finally:
        db.close()


@router.post("/report", summary="Report an account from a private chat (reason only, never chat contents)")
def report_user(req: UserReportRequest, current_user: models.User = Depends(get_current_user)):
    from app import safety

    if req.reason not in safety.REPORT_REASONS:
        raise HTTPException(status_code=400, detail=f"Reason must be one of: {', '.join(safety.REPORT_REASONS)}.")
    if req.reported_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You can't report yourself.")
    name = req.reported_name.strip()[:120]
    if not name:
        raise HTTPException(status_code=400, detail="Who are you reporting?")

    db = SessionLocal()
    try:
        if safety.active_suspension(db, current_user.id):
            raise HTTPException(status_code=403, detail="Suspended accounts can't file reports. You can still block people.")
        if req.reported_user_id and not db.query(models.User).filter(models.User.id == req.reported_user_id).first():
            raise HTTPException(status_code=404, detail="Reported user not found.")
        result = safety.file_report(db, current_user, req.reported_user_id, name, req.reason, (req.note or "").strip()[:1000])
        # auto_suspended stays internal: reporters aren't told what happened to the account.
        return {"status": "success", "message": "Report submitted for admin review.", "report_id": result["report_id"]}
    finally:
        db.close()
