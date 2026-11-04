"""Admin moderation of the public Community: delete/restore, official replies, verify.

Every write is recorded in the audit log under the acting admin's name, and the
affected student gets an in-app notification.
"""
import datetime
import json
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func

from app import audit, models
from app.admin_templates import DELETE_REASONS, REPLY_TEMPLATES
from app.community_knowledge import POPULAR_THRESHOLD, dataset_source, notify, upvote_count
from app.database import SessionLocal
from app.routers.admin_router import require_admin_user
from app.routers.community_v2 import MAX_BODY, _clean, _parse_id, _relative

router = APIRouter(prefix="/api/admin", tags=["8. Admin Console & Operations"], dependencies=[Depends(require_admin_user)])

VIEWS = {"all", "unanswered", "popular", "verified", "dataset", "deleted"}


class DeleteRequest(BaseModel):
    reason: str
    note: Optional[str] = ""


class OfficialReplyRequest(BaseModel):
    body: str
    parent_id: Optional[str] = None  # "c-<n>" to answer a specific reply
    template_key: Optional[str] = None  # recorded in the audit log when a template was used


class VerifyRequest(BaseModel):
    verified: bool


def _admin_names(db) -> dict:
    return {u.id: (u.name or u.email) for u in db.query(models.User).filter(models.User.role == "admin").all()}


def _who(user: Optional[models.User], label: Optional[str], admins: dict) -> str:
    if user and user.role == "admin":
        return f"MITra Official · {admins.get(user.id, 'admin')}"
    if user:
        return user.name
    return f"{label or 'Former member'} (sample)" if label else "Former member"


def _serialize(post: models.CommunityPost, scores: dict, admins: dict, upvotes: int) -> dict:
    children = defaultdict(list)
    for c in sorted(post.comments, key=lambda c: c.created_at or datetime.datetime.min):
        children[c.parent_id].append(c)

    def deleted_info(obj):
        if not obj.deleted_at:
            return None
        by = admins.get(obj.deleted_by)
        return {"by": f"Admin {by}" if by else "Author", "reason": obj.delete_reason, "time": _relative(obj.deleted_at)}

    def build(c):
        return {
            "id": f"c-{c.id}",
            "author": _who(c.author, c.author_label, admins),
            "body": c.body,
            "time": _relative(c.created_at),
            "votes": scores.get(("comment", c.id), 0) + (c.seed_score or 0),
            "is_official": bool(c.is_official),
            "edited": c.edited_at is not None,
            "deleted": deleted_info(c),
            "replies": [build(r) for r in children[c.id]],
        }

    live_answers = [c for c in children[None] if not c.deleted_at]
    return {
        "id": f"p-{post.id}",
        "title": post.title,
        "body": post.body,
        "tags": json.loads(post.tags_json or "[]"),
        "author": _who(post.author, post.author_label, admins),
        "time": _relative(post.created_at),
        "votes": scores.get(("post", post.id), 0) + (post.seed_score or 0),
        "upvotes": upvotes,
        "answer_count": len(live_answers),
        "has_official_reply": any(c.is_official and not c.deleted_at for c in post.comments),
        "verified": bool(post.verified),
        "verified_by": admins.get(post.verified_by),
        "in_dataset": bool(post.in_dataset) and not post.deleted_at,
        "dataset_source": dataset_source(post),
        "deleted": deleted_info(post),
        "answers": [build(c) for c in children[None]],
    }


def _scores(db) -> dict:
    out = {}
    for t, tid, total in (
        db.query(models.CommunityVote.target_type, models.CommunityVote.target_id, func.sum(models.CommunityVote.value))
        .group_by(models.CommunityVote.target_type, models.CommunityVote.target_id)
        .all()
    ):
        out[(t, tid)] = int(total or 0)
    return out


def _upvotes(db) -> dict:
    return dict(
        db.query(models.CommunityVote.target_id, func.count(models.CommunityVote.id))
        .filter(models.CommunityVote.target_type == "post", models.CommunityVote.value == 1)
        .group_by(models.CommunityVote.target_id)
        .all()
    )


def _one(db, post: models.CommunityPost) -> dict:
    db.expire_all()
    return _serialize(post, _scores(db), _admin_names(db), upvote_count(db, post.id))


def _get_post(db, raw_id: str) -> models.CommunityPost:
    post = db.query(models.CommunityPost).filter(models.CommunityPost.id == _parse_id(raw_id, "p")).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    return post


def _get_comment(db, raw_id: str) -> models.CommunityComment:
    c = db.query(models.CommunityComment).filter(models.CommunityComment.id == _parse_id(raw_id, "c")).first()
    if not c:
        raise HTTPException(status_code=404, detail="Reply not found.")
    return c


def _reason(req: DeleteRequest) -> str:
    if req.reason not in DELETE_REASONS:
        raise HTTPException(status_code=400, detail=f"Reason must be one of: {', '.join(DELETE_REASONS)}.")
    note = (req.note or "").strip()[:300]
    return f"{req.reason}: {note}" if note else req.reason


@router.get("/community/templates", summary="Reply templates and delete reasons")
def templates():
    return {"reply_templates": REPLY_TEMPLATES, "delete_reasons": DELETE_REASONS, "popular_threshold": POPULAR_THRESHOLD}


@router.get("/community/posts", summary="Every community post with full threads, including deleted ones")
def list_posts(view: str = "all"):
    if view not in VIEWS:
        raise HTTPException(status_code=400, detail=f"view must be one of {sorted(VIEWS)}")
    db = SessionLocal()
    try:
        posts = db.query(models.CommunityPost).order_by(models.CommunityPost.created_at.desc()).all()
        scores, admins, upvotes = _scores(db), _admin_names(db), _upvotes(db)
        items = [_serialize(p, scores, admins, upvotes.get(p.id, 0)) for p in posts]
        live = [i for i in items if not i["deleted"]]
        counts = {
            "all": len(live),
            "unanswered": sum(1 for i in live if i["answer_count"] == 0),
            "popular": sum(1 for i in live if i["upvotes"] >= POPULAR_THRESHOLD),
            "verified": sum(1 for i in live if i["verified"]),
            "dataset": sum(1 for i in live if i["in_dataset"]),
            "deleted": len(items) - len(live),
        }
        pick = {
            "all": live,
            "unanswered": [i for i in live if i["answer_count"] == 0],
            "popular": [i for i in live if i["upvotes"] >= POPULAR_THRESHOLD],
            "verified": [i for i in live if i["verified"]],
            "dataset": [i for i in live if i["in_dataset"]],
            "deleted": [i for i in items if i["deleted"]],
        }[view]
        return {"posts": pick, "counts": counts}
    finally:
        db.close()


@router.post("/community/posts/{post_id}/reply", summary="Reply as MITra Official (template or written)")
def official_reply(post_id: str, req: OfficialReplyRequest, admin: models.User = Depends(require_admin_user)):
    body = _clean(req.body, MAX_BODY, "Reply")
    if req.template_key and req.template_key not in {t["key"] for t in REPLY_TEMPLATES}:
        raise HTTPException(status_code=400, detail="Unknown template.")
    db = SessionLocal()
    try:
        post = _get_post(db, post_id)
        if post.deleted_at:
            raise HTTPException(status_code=400, detail="Restore the post before replying to it.")
        parent = None
        if req.parent_id:
            parent = _get_comment(db, req.parent_id)
            if parent.post_id != post.id or parent.deleted_at:
                raise HTTPException(status_code=400, detail="That reply isn't part of this post.")
        db.add(models.CommunityComment(post_id=post.id, parent_id=parent.id if parent else None, author_id=admin.id, body=body, is_official=True))
        audit.record(
            db, admin, "community.official_reply",
            f'Replied as MITra Official on "{post.title}"' + (f" (template: {req.template_key})" if req.template_key else ""),
            "post", post_id, {"template_key": req.template_key, "parent_id": req.parent_id, "body": body[:500]},
        )
        notify(db, post.author_id, "MITra Official replied to your question", f'"{post.title}": {body[:160]}', "official_reply", "✅")
        if parent and parent.author_id and parent.author_id != post.author_id:
            notify(db, parent.author_id, "MITra Official replied to you", body[:160], "official_reply", "✅")
        db.commit()
        return _one(db, post)
    finally:
        db.close()


@router.post("/community/posts/{post_id}/verify", summary="Mark a post verified (adds it to the chatbot dataset) or unverify it")
def verify_post(post_id: str, req: VerifyRequest, admin: models.User = Depends(require_admin_user)):
    db = SessionLocal()
    try:
        post = _get_post(db, post_id)
        if post.deleted_at:
            raise HTTPException(status_code=400, detail="Deleted posts can't be verified.")
        if bool(post.verified) == req.verified:
            return _one(db, post)
        if req.verified:
            post.verified, post.verified_by, post.verified_at, post.in_dataset = True, admin.id, datetime.datetime.utcnow(), True
            audit.record(db, admin, "community.verify", f'Verified "{post.title}" and added it to the chatbot dataset', "post", post_id)
            notify(db, post.author_id, "Your question was verified", f'The MITra team verified "{post.title}". It now helps the chatbot answer others.', "post_verified", "✔️")
        else:
            post.verified, post.verified_by, post.verified_at = False, None, None
            # Stays in the dataset only if it independently earned the popular threshold.
            still_popular = upvote_count(db, post.id) >= POPULAR_THRESHOLD
            post.in_dataset = still_popular
            audit.record(
                db, admin, "community.unverify",
                f'Removed verification from "{post.title}"' + ("" if still_popular else " and took it out of the chatbot dataset"),
                "post", post_id,
            )
        db.commit()
        return _one(db, post)
    finally:
        db.close()


@router.post("/community/posts/{post_id}/delete", summary="Delete any post (soft delete, with a reason)")
def delete_post(post_id: str, req: DeleteRequest, admin: models.User = Depends(require_admin_user)):
    reason = _reason(req)
    db = SessionLocal()
    try:
        post = _get_post(db, post_id)
        if post.deleted_at:
            raise HTTPException(status_code=400, detail="Already deleted.")
        post.deleted_at, post.deleted_by, post.delete_reason = datetime.datetime.utcnow(), admin.id, reason
        audit.record(db, admin, "community.delete_post", f'Deleted "{post.title}" ({reason})', "post", post_id, {"title": post.title, "body": post.body[:500]})
        notify(db, post.author_id, "Your question was removed", f'"{post.title}" was removed by the MITra team. Reason: {reason}.', "post_deleted", "🗑️")
        db.commit()
        return _one(db, post)
    finally:
        db.close()


@router.post("/community/posts/{post_id}/restore", summary="Undo a post deletion")
def restore_post(post_id: str, admin: models.User = Depends(require_admin_user)):
    db = SessionLocal()
    try:
        post = _get_post(db, post_id)
        if not post.deleted_at:
            raise HTTPException(status_code=400, detail="This post isn't deleted.")
        prev = post.delete_reason
        post.deleted_at, post.deleted_by, post.delete_reason = None, None, None
        audit.record(db, admin, "community.restore_post", f'Restored "{post.title}" (was: {prev})', "post", post_id)
        db.commit()
        return _one(db, post)
    finally:
        db.close()


@router.post("/community/comments/{comment_id}/delete", summary="Delete any answer or reply (soft delete, with a reason)")
def delete_comment(comment_id: str, req: DeleteRequest, admin: models.User = Depends(require_admin_user)):
    reason = _reason(req)
    db = SessionLocal()
    try:
        c = _get_comment(db, comment_id)
        if c.deleted_at:
            raise HTTPException(status_code=400, detail="Already deleted.")
        c.deleted_at, c.deleted_by, c.delete_reason = datetime.datetime.utcnow(), admin.id, reason
        audit.record(db, admin, "community.delete_comment", f'Deleted a reply on "{c.post.title}" ({reason})', "comment", comment_id, {"body": c.body[:500]})
        notify(db, c.author_id, "Your reply was removed", f'Your reply on "{c.post.title}" was removed by the MITra team. Reason: {reason}.', "post_deleted", "🗑️")
        db.commit()
        return _one(db, c.post)
    finally:
        db.close()


@router.post("/community/comments/{comment_id}/restore", summary="Undo a reply deletion")
def restore_comment(comment_id: str, admin: models.User = Depends(require_admin_user)):
    db = SessionLocal()
    try:
        c = _get_comment(db, comment_id)
        if not c.deleted_at:
            raise HTTPException(status_code=400, detail="This reply isn't deleted.")
        c.deleted_at, c.deleted_by, c.delete_reason = None, None, None
        audit.record(db, admin, "community.restore_comment", f'Restored a reply on "{c.post.title}"', "comment", comment_id)
        db.commit()
        return _one(db, c.post)
    finally:
        db.close()


@router.get("/audit", summary="Audit log of admin and automatic actions, newest first")
def audit_log(action: Optional[str] = None, admin: Optional[str] = None, limit: int = 200):
    db = SessionLocal()
    try:
        q = db.query(models.AdminAuditLog)
        if action:
            q = q.filter(models.AdminAuditLog.action.like(f"{action}%"))
        if admin:
            q = q.filter(models.AdminAuditLog.admin_name == admin)
        rows = q.order_by(models.AdminAuditLog.id.desc()).limit(max(1, min(limit, 1000))).all()
        names = sorted({r[0] for r in db.query(models.AdminAuditLog.admin_name).distinct().all()})
        return {
            "entries": [
                {
                    "id": r.id,
                    "admin": r.admin_name,
                    "action": r.action,
                    "target_type": r.target_type,
                    "target_id": r.target_id,
                    "summary": r.summary,
                    "details": json.loads(r.details_json) if r.details_json else None,
                    "time": _relative(r.created_at),
                    "at": r.created_at.isoformat() + "Z" if r.created_at else None,
                }
                for r in rows
            ],
            "admins": names,
        }
    finally:
        db.close()
