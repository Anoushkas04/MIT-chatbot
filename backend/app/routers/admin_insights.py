"""Admin monitoring page, account directory and the insights dashboard.

Everything here is read-only and aggregated from the live database.
"""
import datetime
import json
import statistics
from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, text

from app import models, safety
from app.config import ADMIN_ACCOUNTS, AUTH_DEV_MODE, GEMINI_API_KEY, SESSION_SECRET, SUPABASE_ANON_KEY, SUPABASE_URL
from app.database import SessionLocal
from app.email_service import is_smtp_configured
from app.llm import is_valid_key
from app.rag import index
from app.routers.admin_router import require_admin_user
from app.routers.community_v2 import _relative

router = APIRouter(prefix="/api/admin", tags=["8. Admin Console & Operations"], dependencies=[Depends(require_admin_user)])


def _now():
    return datetime.datetime.utcnow()


def _daily(dates, days: int) -> list:
    """[{date, value}] for each of the last `days` days, zero-filled."""
    counts = Counter(d.date() for d in dates if d)
    start = _now().date() - datetime.timedelta(days=days - 1)
    return [{"date": (start + datetime.timedelta(days=i)).isoformat(), "value": counts.get(start + datetime.timedelta(days=i), 0)} for i in range(days)]


def _active_student_ids(db, since) -> set:
    ids = set()
    for model, col in ((models.CommunityPost, models.CommunityPost.author_id), (models.CommunityComment, models.CommunityComment.author_id)):
        ids |= {r[0] for r in db.query(col).filter(model.created_at >= since, col.isnot(None)).distinct()}
    ids |= {r[0] for r in db.query(models.CommunityVote.user_id).filter(models.CommunityVote.created_at >= since).distinct()}
    ids |= {r[0] for r in db.query(models.ChatSession.user_id).filter(models.ChatSession.updated_at >= since, models.ChatSession.user_id.isnot(None)).distinct()}
    return ids


@router.get("/monitoring", summary="Platform overview: accounts, moderation queue, dataset and health")
def monitoring():
    db = SessionLocal()
    try:
        week = _now() - datetime.timedelta(days=7)
        students = db.query(models.User).filter(models.User.role == "student")
        student_ids = {u.id for u in students.all()}

        needs_review = []
        for s in db.query(models.Suspension).filter(models.Suspension.status == "active", models.Suspension.source == "auto_reports", models.Suspension.reviewed.is_(False)).all():
            if not safety.active_suspension(db, s.user_id):
                continue
            u = db.query(models.User).filter(models.User.id == s.user_id).first()
            needs_review.append({"user_id": s.user_id, "name": u.name if u else "Unknown", "reporters": safety.open_reporter_count(db, s.user_id), "since": _relative(s.starts_at)})

        active_susp = db.query(models.Suspension).filter(models.Suspension.status == "active").all()
        suspended_now = len({s.user_id for s in active_susp if safety.active_suspension(db, s.user_id)})

        try:
            db.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False
        try:
            from app.rag.store import get_store

            store_chunks = len(get_store().chunks)
        except Exception:
            store_chunks = None
        m = index.meta()

        checks = [
            {"key": "database", "label": "Database reachable", "ok": db_ok},
            {"key": "index", "label": "Chatbot document index loaded", "ok": store_chunks is not None, "detail": f"{store_chunks} chunks" if store_chunks is not None else "No index yet: rebuild it from Dataset"},
            {"key": "embedder", "label": "Index matches the current embedder", "ok": not m or m.get("embedder") in (None, index.current_embedder()), "detail": f"{m.get('embedder') or 'unknown'} → now {index.current_embedder()}"},
            {"key": "gemini", "label": "Gemini API key set (better answers and search)", "ok": is_valid_key(GEMINI_API_KEY), "warn_only": True},
            {"key": "email", "label": "Sign-in emails can be sent", "ok": is_smtp_configured() or bool(SUPABASE_URL and SUPABASE_ANON_KEY)},
            {"key": "secret", "label": "Session secret set (logins survive restarts)", "ok": bool(SESSION_SECRET)},
            {"key": "devmode", "label": "Dev mode is off (codes never shown on screen)", "ok": not AUTH_DEV_MODE},
            {"key": "admins", "label": "Official admin accounts", "ok": bool(ADMIN_ACCOUNTS), "detail": ", ".join(ADMIN_ACCOUNTS.values())},
        ]
        recent = db.query(models.AdminAuditLog).order_by(models.AdminAuditLog.id.desc()).limit(8).all()
        return {
            "students": {
                "total": len(student_ids),
                "new_7d": students.filter(models.User.created_at >= week).count(),
                "active_7d": len(_active_student_ids(db, week) & student_ids),
                "suspended": suspended_now,
            },
            "moderation": {
                "needs_review": needs_review,
                "open_report_accounts": db.query(models.UserReport.reported_user_id, models.UserReport.reported_name).filter(models.UserReport.status == "open").distinct().count(),
                "pending_pleas": db.query(models.Plea).filter(models.Plea.status == "pending").count(),
                "pending_appeals": db.query(models.AccountAppeal).filter(models.AccountAppeal.status == "pending").count(),
                "unanswered_questions": sum(
                    1 for p in db.query(models.CommunityPost).filter(models.CommunityPost.deleted_at.is_(None)).all() if not any(c.deleted_at is None for c in p.comments)
                ),
            },
            "dataset": {
                "files": len([p for p in index.DOCS_DIR.iterdir() if p.is_file() and not p.name.startswith(".")]) if index.DOCS_DIR.exists() else 0,
                "chunks": m.get("total_chunks"),
                "built_at": m.get("built_at"),
                "embedder": m.get("embedder"),
                "community_posts": db.query(models.CommunityPost).filter(models.CommunityPost.in_dataset.is_(True), models.CommunityPost.deleted_at.is_(None)).count(),
                "rebuilding": index.rebuild_state["running"],
            },
            "health": checks,
            "recent_actions": [{"admin": e.admin_name, "summary": e.summary, "time": _relative(e.created_at)} for e in recent],
        }
    finally:
        db.close()


@router.get("/accounts", summary="Student accounts with activity, reports, warnings and suspension state")
def accounts(q: Optional[str] = None, filter: str = "all"):
    if filter not in ("all", "suspended", "reported", "warned", "disabled"):
        raise HTTPException(status_code=400, detail="filter must be all, suspended, reported, warned or disabled")
    db = SessionLocal()
    try:
        query = db.query(models.User).filter(models.User.role == "student")
        if q and q.strip():
            term = f"%{q.strip()}%"
            query = query.filter((models.User.name.ilike(term)) | (models.User.email.ilike(term)) | (models.User.registration_number.ilike(term)))
        users = query.order_by(models.User.created_at.desc()).limit(300).all()
        ids = [u.id for u in users]

        def count_by(col, *conds):
            return dict(db.query(col, func.count()).filter(col.in_(ids), *conds).group_by(col).all()) if ids else {}

        posts = count_by(models.CommunityPost.author_id, models.CommunityPost.deleted_at.is_(None))
        comments = count_by(models.CommunityComment.author_id, models.CommunityComment.deleted_at.is_(None))
        reports_total = count_by(models.UserReport.reported_user_id)
        reports_open = count_by(models.UserReport.reported_user_id, models.UserReport.status == "open")
        warnings = count_by(models.AccountWarning.user_id)

        out = []
        for u in users:
            s = safety.active_suspension(db, u.id)
            row = {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "registration_number": u.registration_number,
                "department": u.department or "",
                "joined": _relative(u.created_at),
                "posts": posts.get(u.id, 0),
                "replies": comments.get(u.id, 0),
                "reports": reports_total.get(u.id, 0),
                "open_reports": reports_open.get(u.id, 0),
                "warnings": warnings.get(u.id, 0),
                "strikes": u.strike_count or 0,
                "status": u.status,
                "suspended": {"reason": s.reason, "ends_at": s.ends_at.isoformat() + "Z" if s.ends_at else None, "source": s.source} if s else None,
            }
            keep = {
                "all": True,
                "suspended": row["suspended"] is not None,
                "reported": row["reports"] > 0,
                "warned": row["warnings"] > 0,
                "disabled": u.status != "active",
            }[filter]
            if keep:
                out.append(row)
        return {"accounts": out, "total_students": db.query(models.User).filter(models.User.role == "student").count()}
    finally:
        db.close()


@router.get("/insights", summary="Platform insights for the last N days (7, 30 or 90)")
def insights(days: int = 30):
    if days not in (7, 30, 90):
        raise HTTPException(status_code=400, detail="days must be 7, 30 or 90")
    db = SessionLocal()
    try:
        since = _now() - datetime.timedelta(days=days)

        # --- Chatbot ---
        asked = [m.created_at for m in db.query(models.ChatMessage.created_at).filter(models.ChatMessage.sender_role == "user", models.ChatMessage.created_at >= since)]
        answers = db.query(models.ChatMessage.confidence).filter(models.ChatMessage.sender_role == "assistant", models.ChatMessage.created_at >= since).all()
        low = sum(1 for (c,) in answers if c in ("low", "no_evidence"))
        logs = db.query(models.QueryAnalyticsLog).filter(models.QueryAnalyticsLog.created_at >= since).all()
        gaps = (
            db.query(models.KnowledgeGap)
            .filter(models.KnowledgeGap.status != "verified")
            .order_by(models.KnowledgeGap.frequency.desc())
            .limit(8)
            .all()
        )
        feedback = db.query(models.SystemFeedback).filter(models.SystemFeedback.created_at >= since).all()
        signals = db.query(models.LearningSignal.explicit_rating).filter(models.LearningSignal.created_at >= since).all()

        # --- Community ---
        posts = db.query(models.CommunityPost).filter(models.CommunityPost.created_at >= since).all()
        comments = db.query(models.CommunityComment).filter(models.CommunityComment.created_at >= since).all()
        live_posts = [p for p in posts if not p.deleted_at]
        first_answer_hours = []
        for p in live_posts:
            firsts = [c.created_at for c in p.comments if c.parent_id is None and c.created_at and p.created_at and c.created_at >= p.created_at]
            if firsts:
                first_answer_hours.append((min(firsts) - p.created_at).total_seconds() / 3600)
        tags = Counter()
        for p in live_posts:
            tags.update(json.loads(p.tags_json or "[]"))

        # --- Safety & accounts ---
        reports = db.query(models.UserReport).filter(models.UserReport.created_at >= since).all()
        signups = [u.created_at for u in db.query(models.User.created_at).filter(models.User.role == "student", models.User.created_at >= since)]

        return {
            "days": days,
            "chat": {
                "questions": len(asked),
                "per_day": _daily(asked, days),
                "low_confidence_rate": round(low / len(answers), 3) if answers else None,
                "answers": len(answers),
                "topics": Counter(l.topic or "General" for l in logs).most_common(8),
                "intents": Counter(l.intent or "unknown" for l in logs).most_common(6),
                "knowledge_gaps": [{"question": g.query_text, "times_asked": g.frequency, "category": g.category, "status": g.status} for g in gaps],
                "feedback_count": len(feedback),
                "avg_rating": round(statistics.mean(f.rating for f in feedback), 2) if feedback else None,
                "helpful_rate": round(sum(1 for (r,) in signals if r and r > 0) / len(signals), 3) if signals else None,
            },
            "community": {
                "questions": len(live_posts),
                "answers": sum(1 for c in comments if not c.deleted_at),
                "questions_per_day": _daily([p.created_at for p in live_posts], days),
                "answers_per_day": _daily([c.created_at for c in comments if not c.deleted_at], days),
                "unanswered_rate": round(sum(1 for p in live_posts if not any(c.deleted_at is None for c in p.comments)) / len(live_posts), 3) if live_posts else None,
                "median_hours_to_first_answer": round(statistics.median(first_answer_hours), 1) if first_answer_hours else None,
                "official_replies": sum(1 for c in comments if c.is_official and not c.deleted_at),
                "removed": sum(1 for p in posts if p.deleted_at) + sum(1 for c in comments if c.deleted_at),
                "top_tags": tags.most_common(8),
            },
            "safety": {
                "reports": len(reports),
                "by_reason": Counter(r.reason for r in reports).most_common(),
                "warnings": db.query(models.AccountWarning).filter(models.AccountWarning.created_at >= since).count(),
                "suspensions": db.query(models.Suspension).filter(models.Suspension.starts_at >= since).count(),
            },
            "accounts": {"signups": len(signups), "signups_per_day": _daily(signups, days)},
        }
    finally:
        db.close()
