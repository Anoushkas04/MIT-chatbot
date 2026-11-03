import datetime
from typing import Optional
from fastapi import APIRouter, Query
from app.database import SessionLocal
from app import models
from app.calendar_engine import get_personalized_notifications

router = APIRouter(prefix="/api/notifications", tags=["6. Notifications & Alerts"])


@router.get("", summary="Get intelligent personalized notifications driven by canonical academic timeline")
def get_notifications(
    user_id: str = "guest",
    role: str = "student",
    dept: Optional[str] = None,
    year: Optional[str] = None
):
    return get_personalized_notifications(user_id=user_id, role=role, department=dept, academic_year=year)


@router.post("/{state_id}/read", summary="Mark a single notification as read")
def mark_notification_read(state_id: int):
    db = SessionLocal()
    try:
        state = db.query(models.UserNotificationState).filter(models.UserNotificationState.id == state_id).first()
        if state:
            state.is_read = True
            state.read_at = datetime.datetime.utcnow()
            db.commit()
            return {"status": "success", "state_id": state_id, "is_read": True}
        return {"status": "error", "message": "Notification state not found."}
    finally:
        db.close()


@router.post("/{state_id}/dismiss", summary="Dismiss a notification from drawer")
def dismiss_notification(state_id: int):
    db = SessionLocal()
    try:
        state = db.query(models.UserNotificationState).filter(models.UserNotificationState.id == state_id).first()
        if state:
            state.is_dismissed = True
            state.dismissed_at = datetime.datetime.utcnow()
            db.commit()
            return {"status": "success", "state_id": state_id, "is_dismissed": True}
        return {"status": "error", "message": "Notification state not found."}
    finally:
        db.close()


@router.post("/{state_id}/dismiss-popup", summary="Dismiss popup toast alert so it does not reappear")
def dismiss_popup_notification(state_id: int):
    db = SessionLocal()
    try:
        state = db.query(models.UserNotificationState).filter(models.UserNotificationState.id == state_id).first()
        if state:
            state.is_popup_dismissed = True
            db.commit()
            return {"status": "success", "state_id": state_id, "is_popup_dismissed": True}
        return {"status": "error", "message": "Notification state not found."}
    finally:
        db.close()


@router.post("/dismiss-all-popups", summary="Dismiss all active popup toast alerts for a user so no old popups reappear after visiting notification center")
def dismiss_all_popups(user_id: str = "guest"):
    db = SessionLocal()
    try:
        db.query(models.UserNotificationState).filter(
            models.UserNotificationState.user_id == user_id,
            models.UserNotificationState.is_popup_dismissed == False
        ).update({
            "is_popup_dismissed": True
        })
        db.commit()
        return {"status": "success", "message": "All active popup toasts dismissed permanently for user."}
    finally:
        db.close()


@router.post("/read-all", summary="Mark all notifications as read for a user")
def mark_all_read(user_id: str = "guest"):
    db = SessionLocal()
    try:
        db.query(models.UserNotificationState).filter(
            models.UserNotificationState.user_id == user_id,
            models.UserNotificationState.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.datetime.utcnow()
        })
        db.commit()
        return {"status": "success", "message": "All notifications marked as read."}
    finally:
        db.close()
