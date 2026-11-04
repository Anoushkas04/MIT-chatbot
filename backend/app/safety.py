"""Reports, warnings and suspensions.

Privacy: reports carry only the reporter's chosen reason and optional note. Private
chats are never sent to the server, so admins decide on reasons alone.

An account reported by AUTO_SUSPEND_REPORTERS distinct accounts (open reports) is
suspended automatically until an admin reviews it.
"""
import datetime
from typing import Optional

from app import audit, models
from app.community_knowledge import notify

REPORT_REASONS = [
    "Harassment or bullying",
    "Hate speech",
    "Nudity or sexual content",
    "Threats or violence",
    "Spam or scam",
    "Impersonation",
    "Self-harm concern",
    "Other",
]

AUTO_SUSPEND_REPORTERS = 10
SUSPENSION_DAYS = [1, 3, 7, 30]  # or None: until an admin lifts it


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _sync_user_flags(db, user_id: str) -> None:
    """Keeps the legacy User.is_suspended / suspended_until columns in step."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return
    s = active_suspension(db, user_id, sync=False)
    user.is_suspended = s is not None
    user.suspended_at = s.starts_at if s else None
    user.suspended_until = s.ends_at if s else None


def active_suspension(db, user_id: str, sync: bool = True) -> Optional[models.Suspension]:
    """The account's current suspension, expiring any whose period has ended."""
    rows = db.query(models.Suspension).filter(models.Suspension.user_id == user_id, models.Suspension.status == "active").all()
    current, changed = None, False
    for s in rows:
        if s.ends_at and _now() >= s.ends_at:
            s.status, changed = "expired", True
        else:
            current = s
    if changed:
        if sync:
            _sync_user_flags(db, user_id)
        db.commit()
    return current


def suspension_message(s: models.Suspension) -> str:
    until = f"until {s.ends_at.strftime('%b %d, %Y')}" if s.ends_at else "until the MITra team reviews it"
    return f"Your account is suspended from posting, replying, voting and reporting {until}."


def suspend(db, user_id: str, reason: str, days: Optional[int], admin: Optional[models.User], source: str = "admin") -> models.Suspension:
    for s in db.query(models.Suspension).filter(models.Suspension.user_id == user_id, models.Suspension.status == "active").all():
        s.status, s.lifted_by, s.lifted_at = "lifted", admin.id if admin else None, _now()  # replaced by this one
    s = models.Suspension(
        user_id=user_id,
        source=source,
        reason=reason,
        starts_at=_now(),
        ends_at=_now() + datetime.timedelta(days=days) if days else None,
        status="active",
        reviewed=admin is not None,
        admin_id=admin.id if admin else None,
    )
    db.add(s)
    db.flush()
    _sync_user_flags(db, user_id)
    when = f"for {days} day{'s' if days != 1 else ''}" if days else "until the MITra team lifts it"
    notify(
        db, user_id, "Your account has been suspended",
        f"Reason: {reason}. You're suspended {when}. You can still read MITra, and you can send the team a plea from the banner at the top of the app.",
        "suspended", "⛔",
    )
    return s


def lift(db, s: models.Suspension, admin: models.User, why: str) -> None:
    s.status, s.lifted_by, s.lifted_at, s.reviewed = "lifted", admin.id, _now(), True
    # Nothing left to appeal: close a plea still waiting on this suspension.
    for p in db.query(models.Plea).filter(models.Plea.suspension_id == s.id, models.Plea.status == "pending").all():
        p.status, p.admin_id, p.decided_at, p.decision_note = "closed", admin.id, _now(), "Suspension lifted"
    db.flush()
    _sync_user_flags(db, s.user_id)
    notify(db, s.user_id, "Your suspension has been lifted", why, "suspension_lifted", "✅")


def open_reporter_count(db, user_id: str) -> int:
    return (
        db.query(models.UserReport.reporter_id)
        .filter(models.UserReport.reported_user_id == user_id, models.UserReport.status == "open")
        .distinct()
        .count()
    )


def file_report(db, reporter: models.User, reported_user_id: Optional[str], reported_name: str, reason: str, note: str) -> dict:
    """Records (or updates) the reporter's open report and applies the auto-suspend rule."""
    q = db.query(models.UserReport).filter(models.UserReport.reporter_id == reporter.id, models.UserReport.status == "open")
    q = q.filter(models.UserReport.reported_user_id == reported_user_id) if reported_user_id else q.filter(
        models.UserReport.reported_user_id.is_(None), models.UserReport.reported_name == reported_name
    )
    report = q.first()
    if report:  # one open report per reporter and account: refresh it instead of stacking duplicates
        report.reason, report.note, report.created_at = reason, note, _now()
    else:
        report = models.UserReport(reporter_id=reporter.id, reported_user_id=reported_user_id, reported_name=reported_name, reason=reason, note=note)
        db.add(report)
    db.flush()

    auto_suspended = False
    if reported_user_id:
        count = open_reporter_count(db, reported_user_id)
        if count >= AUTO_SUSPEND_REPORTERS and active_suspension(db, reported_user_id) is None:
            suspend(db, reported_user_id, f"Reported by {count} different students; pending review by the MITra team", None, None, "auto_reports")
            audit.record(db, None, "safety.auto_suspend", f"Auto-suspended {reported_name}: reported by {count} different accounts.", "user", reported_user_id, {"reporters": count})
            auto_suspended = True
    db.commit()
    return {"report_id": report.id, "auto_suspended": auto_suspended}
