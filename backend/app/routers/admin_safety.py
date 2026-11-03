"""Admin handling of chat reports, warnings, suspensions and pleas.

Admins see each report's reason and note, never chat contents (they're never sent).
Reporter identities aren't shown either: only how many distinct accounts reported.
"""
import datetime
from collections import Counter, defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import audit, models, safety
from app.admin_templates import WARNING_TEMPLATES
from app.community_knowledge import notify
from app.database import SessionLocal
from app.routers.admin_router import require_admin_user
from app.routers.community_v2 import _relative

router = APIRouter(prefix="/api/admin", tags=["8. Admin Console & Operations"], dependencies=[Depends(require_admin_user)])


class DecideRequest(BaseModel):
    target: str  # a user id, or "name:<display name>" for people without an account
    decision: str  # innocent | warn | suspend
    warning_key: Optional[str] = None
    warning_text: Optional[str] = None
    days: Optional[int] = None  # suspend: one of safety.SUSPENSION_DAYS, or omitted for "until lifted"
    reason: Optional[str] = None  # suspend: shown to the student


class LiftRequest(BaseModel):
    note: Optional[str] = ""


class PleaDecision(BaseModel):
    accept: bool
    note: Optional[str] = ""


def _iso(dt):
    return dt.isoformat() + "Z" if dt else None


def _admin_names(db) -> dict:
    return {u.id: (u.name or u.email) for u in db.query(models.User).filter(models.User.role == "admin").all()}


def _suspension_dict(s: Optional[models.Suspension], admins: dict) -> Optional[dict]:
    if not s:
        return None
    return {
        "id": s.id,
        "source": s.source,
        "reason": s.reason,
        "since": _relative(s.starts_at),
        "ends_at": _iso(s.ends_at),
        "reviewed": bool(s.reviewed),
        "by": admins.get(s.admin_id) if s.admin_id else "System",
    }


@router.get("/safety/templates", summary="Warning templates, suspension periods and report reasons")
def safety_templates():
    return {"warning_templates": WARNING_TEMPLATES, "suspension_days": safety.SUSPENSION_DAYS, "report_reasons": safety.REPORT_REASONS, "auto_suspend_reporters": safety.AUTO_SUSPEND_REPORTERS}


@router.get("/reports", summary="Reports grouped by reported account (open or closed)")
def list_reports(status: str = "open"):
    if status not in ("open", "closed"):
        raise HTTPException(status_code=400, detail="status must be open or closed")
    db = SessionLocal()
    try:
        q = db.query(models.UserReport)
        q = q.filter(models.UserReport.status == "open") if status == "open" else q.filter(models.UserReport.status != "open")
        reports = q.order_by(models.UserReport.created_at.desc()).all()
        admins = _admin_names(db)
        groups = defaultdict(list)
        for r in reports:
            groups[r.reported_user_id or f"name:{r.reported_name}"].append(r)

        out = []
        for key, items in groups.items():
            user = db.query(models.User).filter(models.User.id == key).first() if not key.startswith("name:") else None
            s = safety.active_suspension(db, user.id) if user else None
            out.append({
                "target": key,
                "name": user.name if user else items[0].reported_name,
                "has_account": user is not None,
                "department": (user.department or "") if user else "",
                "reporters": len({r.reporter_id for r in items}),
                "reasons": Counter(r.reason for r in items).most_common(),
                "warnings": db.query(models.AccountWarning).filter(models.AccountWarning.user_id == user.id).count() if user else 0,
                "suspension": _suspension_dict(s, admins),
                "needs_review": bool(s and s.source == "auto_reports" and not s.reviewed),
                "latest": _relative(items[0].created_at),
                "reports": [
                    {
                        "id": r.id,
                        "reason": r.reason,
                        "note": r.note or "",
                        "time": _relative(r.created_at),
                        "status": r.status,
                        "decision": r.decision,
                        "decided_by": admins.get(r.decided_by),
                    }
                    for r in items
                ],
            })
        out.sort(key=lambda g: (not g["needs_review"], -g["reporters"]))
        return {"groups": out, "auto_suspend_reporters": safety.AUTO_SUSPEND_REPORTERS}
    finally:
        db.close()


def _close_reports(db, items, admin, decision: str, status: str) -> None:
    reporters = set()
    for r in items:
        r.status, r.decision, r.decided_by, r.decided_at = status, decision, admin.id, datetime.datetime.utcnow()
        reporters.add(r.reporter_id)
    # Reporters learn their report was handled, never what happened to the other account.
    for rid in reporters:
        notify(db, rid, "Thanks for your report", "The MITra team reviewed a report you made. Thank you for helping keep MITra safe.", "report_reviewed", "🛡️")


@router.post("/reports/decide", summary="Decide on a reported account: innocent, warn or suspend")
def decide(req: DecideRequest, admin: models.User = Depends(require_admin_user)):
    if req.decision not in ("innocent", "warn", "suspend"):
        raise HTTPException(status_code=400, detail="decision must be innocent, warn or suspend")
    db = SessionLocal()
    try:
        is_named = req.target.startswith("name:")
        q = db.query(models.UserReport).filter(models.UserReport.status == "open")
        q = q.filter(models.UserReport.reported_user_id.is_(None), models.UserReport.reported_name == req.target[5:]) if is_named else q.filter(models.UserReport.reported_user_id == req.target)
        items = q.all()
        user = None if is_named else db.query(models.User).filter(models.User.id == req.target).first()
        if not is_named and not user:
            raise HTTPException(status_code=404, detail="Account not found.")
        if is_named and req.decision != "innocent":
            raise HTTPException(status_code=400, detail="This person has no MITra account, so the reports can only be dismissed.")
        name = user.name if user else req.target[5:]
        current = safety.active_suspension(db, user.id) if user else None

        if req.decision == "innocent":
            if not items and not current:
                raise HTTPException(status_code=400, detail="There's nothing open to dismiss for this account.")
            _close_reports(db, items, admin, "innocent", "dismissed")
            if current and current.source == "auto_reports":
                safety.lift(db, current, admin, "After review, the reports about your account were dismissed. You have full access again.")
            audit.record(db, admin, "safety.innocent", f"Marked {name} innocent and dismissed {len(items)} report(s)", "user", req.target)

        elif req.decision == "warn":
            text = (req.warning_text or "").strip()
            tpl = next((t for t in WARNING_TEMPLATES if t["key"] == req.warning_key), None)
            if req.warning_key and not tpl:
                raise HTTPException(status_code=400, detail="Unknown warning template.")
            text = text or (tpl["text"] if tpl else "")
            if len(text) < 10:
                raise HTTPException(status_code=400, detail="Choose a warning template or write the warning.")
            db.add(models.AccountWarning(user_id=user.id, template_key=req.warning_key, text=text, admin_id=admin.id))
            notify(db, user.id, "Warning from the MITra team", text, "warning", "⚠️")
            _close_reports(db, items, admin, "warn", "actioned")
            # A warning replaces a pending automatic suspension.
            if current and current.source == "auto_reports" and not current.reviewed:
                safety.lift(db, current, admin, "The team reviewed the reports and sent you a warning instead. You have full access again.")
            audit.record(db, admin, "safety.warn", f"Warned {name}" + (f" ({req.warning_key})" if req.warning_key else ""), "user", req.target, {"text": text})

        else:  # suspend
            if req.days is not None and req.days not in safety.SUSPENSION_DAYS:
                raise HTTPException(status_code=400, detail=f"days must be one of {safety.SUSPENSION_DAYS}, or omitted for 'until lifted'.")
            reason = (req.reason or "").strip()[:300] or "Repeated reports from other students"
            safety.suspend(db, user.id, reason, req.days, admin)
            _close_reports(db, items, admin, "suspend", "actioned")
            period = f"{req.days} day(s)" if req.days else "until lifted"
            audit.record(db, admin, "safety.suspend", f"Suspended {name} for {period}: {reason}", "user", req.target, {"days": req.days, "reason": reason})

        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


@router.get("/suspensions", summary="Active suspensions")
def list_suspensions():
    db = SessionLocal()
    try:
        admins = _admin_names(db)
        rows = db.query(models.Suspension).filter(models.Suspension.status == "active").order_by(models.Suspension.starts_at.desc()).all()
        out = []
        for s in rows:
            if not safety.active_suspension(db, s.user_id):  # expired just now
                continue
            user = db.query(models.User).filter(models.User.id == s.user_id).first()
            plea = db.query(models.Plea).filter(models.Plea.suspension_id == s.id).first()
            out.append({**_suspension_dict(s, admins), "user_id": s.user_id, "name": user.name if user else "Unknown", "plea": plea.status if plea else None})
        return {"suspensions": out}
    finally:
        db.close()


@router.post("/suspensions/{suspension_id}/lift", summary="Lift a suspension early")
def lift_suspension(suspension_id: int, req: LiftRequest, admin: models.User = Depends(require_admin_user)):
    db = SessionLocal()
    try:
        s = db.query(models.Suspension).filter(models.Suspension.id == suspension_id, models.Suspension.status == "active").first()
        if not s:
            raise HTTPException(status_code=404, detail="No active suspension with that id.")
        user = db.query(models.User).filter(models.User.id == s.user_id).first()
        note = (req.note or "").strip()[:300]
        safety.lift(db, s, admin, note or "The MITra team lifted your suspension. You have full access again.")
        audit.record(db, admin, "safety.lift", f"Lifted the suspension on {user.name if user else s.user_id}" + (f": {note}" if note else ""), "user", s.user_id)
        db.commit()
        return {"status": "lifted"}
    finally:
        db.close()


@router.get("/pleas", summary="Pleas from suspended students")
def list_pleas(status: str = "pending"):
    if status not in ("pending", "decided"):
        raise HTTPException(status_code=400, detail="status must be pending or decided")
    db = SessionLocal()
    try:
        admins = _admin_names(db)
        q = db.query(models.Plea)
        q = q.filter(models.Plea.status == "pending") if status == "pending" else q.filter(models.Plea.status != "pending")
        out = []
        for p in q.order_by(models.Plea.created_at.desc()).all():
            s = db.query(models.Suspension).filter(models.Suspension.id == p.suspension_id).first()
            if p.status == "pending" and (not s or s.status != "active"):
                # The suspension already ended (expired or lifted), so there's nothing to decide.
                p.status, p.decision_note = "closed", "Suspension already ended"
                db.commit()
                if status == "pending":
                    continue
            user = db.query(models.User).filter(models.User.id == p.user_id).first()
            reasons = Counter(
                r.reason for r in db.query(models.UserReport).filter(models.UserReport.reported_user_id == p.user_id).all()
            ).most_common()
            out.append({
                "id": p.id,
                "name": user.name if user else "Unknown",
                "user_id": p.user_id,
                "text": p.text,
                "time": _relative(p.created_at),
                "status": p.status,
                "decision_note": p.decision_note,
                "decided_by": admins.get(p.admin_id),
                "suspension": {**(_suspension_dict(s, admins) or {}), "status": s.status if s else None},
                "report_reasons": reasons,
            })
        return {"pleas": out}
    finally:
        db.close()


@router.post("/pleas/{plea_id}/decide", summary="Accept (lift the suspension) or reject a plea")
def decide_plea(plea_id: int, req: PleaDecision, admin: models.User = Depends(require_admin_user)):
    db = SessionLocal()
    try:
        p = db.query(models.Plea).filter(models.Plea.id == plea_id).first()
        if not p or p.status != "pending":
            raise HTTPException(status_code=404, detail="No pending plea with that id.")
        s = db.query(models.Suspension).filter(models.Suspension.id == p.suspension_id).first()
        user = db.query(models.User).filter(models.User.id == p.user_id).first()
        note = (req.note or "").strip()[:500]
        p.status, p.admin_id, p.decision_note, p.decided_at = ("accepted" if req.accept else "rejected"), admin.id, note, datetime.datetime.utcnow()
        name = user.name if user else p.user_id
        if req.accept:
            if s and s.status == "active":
                safety.lift(db, s, admin, note or "The MITra team accepted your plea and lifted your suspension.")
            audit.record(db, admin, "safety.plea_accept", f"Accepted {name}'s plea and lifted the suspension", "user", p.user_id, {"note": note})
        else:
            if s:
                s.reviewed = True
            notify(db, p.user_id, "Your plea was reviewed", note or "The MITra team reviewed your plea. Your suspension stays in place.", "plea_rejected", "📝")
            audit.record(db, admin, "safety.plea_reject", f"Rejected {name}'s plea; suspension stays", "user", p.user_id, {"note": note})
        db.commit()
        return {"status": p.status}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Appeals from disabled accounts (sent from the sign-in page)
# ---------------------------------------------------------------------------

@router.get("/appeals", summary="Appeals from disabled accounts")
def list_appeals(status: str = "pending"):
    if status not in ("pending", "decided"):
        raise HTTPException(status_code=400, detail="status must be pending or decided")
    db = SessionLocal()
    try:
        admins = _admin_names(db)
        q = db.query(models.AccountAppeal)
        q = q.filter(models.AccountAppeal.status == "pending") if status == "pending" else q.filter(models.AccountAppeal.status != "pending")
        out = []
        for a in q.order_by(models.AccountAppeal.created_at.desc()).all():
            user = db.query(models.User).filter(models.User.id == a.user_id).first()
            disabled = (
                db.query(models.AdminAuditLog)
                .filter(models.AdminAuditLog.action == "accounts.disable", models.AdminAuditLog.target_id == a.user_id)
                .order_by(models.AdminAuditLog.id.desc())
                .first()
            )
            out.append({
                "id": a.id,
                "user_id": a.user_id,
                "name": user.name if user else "Unknown",
                "email": user.email if user else "",
                "account_status": user.status if user else None,
                "text": a.text,
                "time": _relative(a.created_at),
                "status": a.status,
                "decision_note": a.decision_note,
                "decided_by": admins.get(a.admin_id),
                "disabled_by": disabled.admin_name if disabled else None,
                "disabled_when": _relative(disabled.created_at) if disabled else None,
            })
        return {"appeals": out}
    finally:
        db.close()


@router.post("/appeals/{appeal_id}/decide", summary="Accept (re-enable the account) or reject an appeal")
def decide_appeal(appeal_id: int, req: PleaDecision, admin: models.User = Depends(require_admin_user)):
    db = SessionLocal()
    try:
        a = db.query(models.AccountAppeal).filter(models.AccountAppeal.id == appeal_id).first()
        if not a or a.status != "pending":
            raise HTTPException(status_code=404, detail="No pending appeal with that id.")
        user = db.query(models.User).filter(models.User.id == a.user_id).first()
        note = (req.note or "").strip()[:500]
        a.status, a.admin_id, a.decision_note, a.decided_at = ("accepted" if req.accept else "rejected"), admin.id, note, datetime.datetime.utcnow()
        name = user.name if user else a.user_id
        if req.accept:
            if user:
                user.status = "active"
            notify(db, a.user_id, "Your appeal was accepted", note or "The MITra team re-enabled your account. Welcome back.", "appeal_accepted", "✅")
            audit.record(db, admin, "accounts.appeal_accept", f"Accepted {name}'s appeal and re-enabled the account", "user", a.user_id, {"note": note})
        else:
            audit.record(db, admin, "accounts.appeal_reject", f"Rejected {name}'s appeal; the account stays disabled", "user", a.user_id, {"note": note})
        db.commit()
        return {"status": a.status}
    finally:
        db.close()
