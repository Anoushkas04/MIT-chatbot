import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from app import audit, models
from app.database import SessionLocal


def require_admin_user(authorization: Optional[str] = Header(None)) -> models.User:
    """RBAC guard for every /api/admin/* endpoint: an active role="admin" account whose
    email is one of the hard-coded config.ADMIN_ACCOUNTS. Raises 401/403 otherwise."""
    from app.routers.auth_router import get_current_admin
    return get_current_admin(authorization)


router = APIRouter(
    prefix="/api/admin",
    tags=["8. Admin Console & Operations"],
    dependencies=[Depends(require_admin_user)],
)


@router.post("/users/toggle-status", summary="Disable or re-enable a student account (blocks sign-in entirely)")
def toggle_user_status(user_id: str, admin: models.User = Depends(require_admin_user)):
    # Separate from suspensions (app/safety.py): a disabled account can't sign in at all.
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        if user.role == "admin":
            raise HTTPException(status_code=400, detail="Admin accounts are fixed in the code and can't be disabled here.")
        user.status = "disabled" if user.status == "active" else "active"
        if user.status == "active":
            # Re-enabled directly: any appeal still waiting is now moot.
            for ap in db.query(models.AccountAppeal).filter(models.AccountAppeal.user_id == user.id, models.AccountAppeal.status == "pending").all():
                ap.status, ap.admin_id, ap.decision_note, ap.decided_at = "accepted", admin.id, "Account re-enabled", datetime.datetime.utcnow()
        audit.record(db, admin, "accounts.disable" if user.status == "disabled" else "accounts.enable",
                     f"{'Disabled' if user.status == 'disabled' else 'Re-enabled'} the account of {user.name}", "user", user.id)
        db.commit()
        return {"status": "success", "user_id": user.id, "new_status": user.status}
    finally:
        db.close()
