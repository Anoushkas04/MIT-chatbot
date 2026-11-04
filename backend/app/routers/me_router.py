"""The signed-in user's own server-side data: notifications from the MITra team, public profile."""
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import models, safety
from app.database import SessionLocal
from app.public_profile import clean_entries, public_profile
from app.routers.auth_router import get_current_user
from app.routers.community_v2 import _relative

router = APIRouter(prefix="/api/me", tags=["1. Authentication & Profile Engine"])


class ProfileEntry(BaseModel):
    name: str
    role: str = ""


class PublicProfileUpdate(BaseModel):
    clubs: List[ProfileEntry] = []
    projects: List[ProfileEntry] = []


@router.put("/profile", summary="Update the clubs and student projects on my public profile")
def update_profile(req: PublicProfileUpdate, me: models.User = Depends(get_current_user)):
    clubs = clean_entries(req.clubs, "clubs")
    projects = clean_entries(req.projects, "student projects")
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == me.id).first()
        user.clubs = json.dumps(clubs)
        user.projects = json.dumps(projects)
        db.commit()
        db.refresh(user)
        return public_profile(user)
    finally:
        db.close()


@router.get("/notifications", summary="My notifications from MITra (official replies, moderation, verification)")
def my_notifications(me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = (
            db.query(models.Notification)
            .filter(models.Notification.user_id == me.id)
            .order_by(models.Notification.id.desc())
            .limit(100)
            .all()
        )
        return {
            "notifications": [
                {
                    "id": f"srv-{n.id}",
                    "category": n.category,
                    "icon": n.icon,
                    "title": n.title,
                    "content": n.content,
                    "read": bool(n.read),
                    "time": _relative(n.created_at),
                }
                for n in rows
            ]
        }
    finally:
        db.close()


@router.post("/notifications/{notification_id}/read", summary="Mark one of my notifications read")
def mark_read(notification_id: str, me: models.User = Depends(get_current_user)):
    if not notification_id.startswith("srv-") or not notification_id[4:].isdigit():
        raise HTTPException(status_code=400, detail="Invalid id.")
    db = SessionLocal()
    try:
        n = db.query(models.Notification).filter(models.Notification.id == int(notification_id[4:]), models.Notification.user_id == me.id).first()
        if not n:
            raise HTTPException(status_code=404, detail="Notification not found.")
        n.read = True
        db.commit()
        return {"status": "read"}
    finally:
        db.close()


@router.post("/notifications/read-all", summary="Mark all my notifications read")
def mark_all_read(me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        db.query(models.Notification).filter(models.Notification.user_id == me.id, models.Notification.read.is_(False)).update({"read": True})
        db.commit()
        return {"status": "read"}
    finally:
        db.close()


class PleaRequest(BaseModel):
    text: str


def _plea_dict(p):
    if not p:
        return None
    return {"status": p.status, "text": p.text, "decision_note": p.decision_note, "time": _relative(p.created_at)}


@router.get("/status", summary="My account standing: active suspension (with plea state) and warning count")
def my_status(me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        s = safety.active_suspension(db, me.id)
        warnings = db.query(models.AccountWarning).filter(models.AccountWarning.user_id == me.id).count()
        if not s:
            return {"suspended": False, "suspension": None, "warnings": warnings}
        plea = db.query(models.Plea).filter(models.Plea.suspension_id == s.id).first()
        return {
            "suspended": True,
            "warnings": warnings,
            "suspension": {
                "id": s.id,
                "reason": s.reason,
                "message": safety.suspension_message(s),
                "ends_at": s.ends_at.isoformat() + "Z" if s.ends_at else None,
                "plea": _plea_dict(plea),
            },
        }
    finally:
        db.close()


@router.post("/plea", summary="Ask the MITra team to review my suspension (one plea per suspension)")
def submit_plea(req: PleaRequest, me: models.User = Depends(get_current_user)):
    text = (req.text or "").strip()
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Please explain your side in at least 20 characters.")
    if len(text) > 2000:
        raise HTTPException(status_code=400, detail="Please keep your plea under 2000 characters.")
    db = SessionLocal()
    try:
        s = safety.active_suspension(db, me.id)
        if not s:
            raise HTTPException(status_code=400, detail="Your account isn't suspended.")
        if db.query(models.Plea).filter(models.Plea.suspension_id == s.id).first():
            raise HTTPException(status_code=409, detail="You've already sent a plea for this suspension.")
        db.add(models.Plea(suspension_id=s.id, user_id=me.id, text=text))
        db.commit()
        return {"status": "pending"}
    finally:
        db.close()
