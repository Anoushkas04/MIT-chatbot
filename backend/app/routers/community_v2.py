"""Public Community Q&A backed by the database (replaces the browser-only feed).

Every route needs a signed-in user. Ids are exposed as "p-<n>" (posts) and "c-<n>"
(comments) so votes and React keys never collide across the two tables.
"""
import datetime
import json
from collections import defaultdict
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func

from app import models
from app.database import SessionLocal
from app.routers.auth_router import get_current_user

router = APIRouter(prefix="/api/community", tags=["5. Student Community & Crowdsourcing"])

OFFICIAL_NAME = "MITra Official"
MAX_TITLE = 200
MAX_BODY = 5000
MAX_TAGS = 5


class PostCreate(BaseModel):
    title: str
    body: str
    tags: List[str] = []


class PostEdit(BaseModel):
    title: str
    body: str


class CommentCreate(BaseModel):
    body: str
    parent_id: Optional[str] = None  # "c-<n>" to reply to a comment; omitted for a top-level answer


class CommentEdit(BaseModel):
    body: str


class VoteRequest(BaseModel):
    target: str  # "p-<n>" or "c-<n>"
    value: int  # 1, -1, or 0 to clear


def _parse_id(raw: str, prefix: str) -> int:
    if not raw or not raw.startswith(f"{prefix}-") or not raw[2:].isdigit():
        raise HTTPException(status_code=400, detail="Invalid id.")
    return int(raw[2:])


def _clean(text: str, limit: int, label: str) -> str:
    text = (text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail=f"{label} can't be empty.")
    if len(text) > limit:
        raise HTTPException(status_code=400, detail=f"{label} must be under {limit} characters.")
    return text


def _relative(dt: Optional[datetime.datetime]) -> str:
    if not dt:
        return ""
    secs = (datetime.datetime.utcnow() - dt).total_seconds()
    if secs < 60:
        return "Just now"
    if secs < 3600:
        return f"{int(secs // 60)}m ago"
    if secs < 86400:
        return f"{int(secs // 3600)}h ago"
    return f"{int(secs // 86400)}d ago"


def _initials(name: str) -> str:
    parts = [p for p in (name or "").replace(".", " ").split() if p]
    return "".join(p[0].upper() for p in parts[:2]) or "?"


def _author(user: Optional[models.User], label: Optional[str]) -> tuple[str, bool]:
    """Display name and whether it's the official (admin) account. Admin names stay internal."""
    if user and user.role == "admin":
        return OFFICIAL_NAME, True
    if user:
        return user.name, False
    return label or "Former member", False


def _ensure_can_write(db, user: models.User) -> None:
    from app.moderation_engine import check_user_suspension_status

    suspended, msg, _ = check_user_suspension_status(db, user.id)
    if suspended:
        raise HTTPException(status_code=403, detail=msg)


def _moderate(db, user: models.User, title: str, body: str) -> None:
    from app.moderation_engine import evaluate_community_content, process_user_strike_and_suspension

    prohibited, category, _reason, confidence = evaluate_community_content(title, body)
    if prohibited and confidence >= 0.80:
        process_user_strike_and_suspension(db, user.id, user.name, category, f"{title}: {body}")
        raise HTTPException(
            status_code=400,
            detail="This can't be published because it breaks the Community Guidelines. Repeated violations may suspend your account.",
        )
    from app.moderation_engine import model_review

    # A model can be wrong, so what only it flags is held back for editing, without a strike
    flagged, category = model_review(title, body)
    if flagged:
        raise HTTPException(
            status_code=400,
            detail=f"This wasn't published because it may break the Community Guidelines ({category}). Please edit it and try again.",
        )


def _vote_maps(db, user_id: str):
    """Score per target and the caller's own vote, for all posts and comments."""
    scores = defaultdict(int)
    for target_type, target_id, total in (
        db.query(models.CommunityVote.target_type, models.CommunityVote.target_id, func.sum(models.CommunityVote.value))
        .group_by(models.CommunityVote.target_type, models.CommunityVote.target_id)
        .all()
    ):
        scores[(target_type, target_id)] = int(total or 0)
    mine = {
        (v.target_type, v.target_id): v.value
        for v in db.query(models.CommunityVote).filter(models.CommunityVote.user_id == user_id).all()
    }
    return scores, mine


def _serialize_post(post: models.CommunityPost, me: models.User, scores, mine) -> dict:
    children = defaultdict(list)
    for c in sorted(post.comments, key=lambda c: c.created_at or datetime.datetime.min):
        children[c.parent_id].append(c)

    def build(c: models.CommunityComment) -> Optional[dict]:
        replies = [r for r in (build(x) for x in children[c.id]) if r is not None]
        if c.deleted_at and not replies:
            return None  # a deleted leaf disappears; a deleted parent stays as a placeholder
        name, official = _author(c.author, c.author_label)
        deleted = c.deleted_at is not None
        return {
            "id": f"c-{c.id}",
            "author": "" if deleted else name,
            "initials": "?" if deleted else ("✓" if official else _initials(name)),
            "time": _relative(c.created_at),
            "body": "" if deleted else c.body,
            "votes": scores[("comment", c.id)] + (c.seed_score or 0),
            "my_vote": mine.get(("comment", c.id), 0),
            "replies": replies,
            "edited": c.edited_at is not None,
            "deleted": deleted,
            "is_official": official or bool(c.is_official),
            "is_mine": c.author_id == me.id and not deleted,
        }

    name, official = _author(post.author, post.author_label)
    return {
        "id": f"p-{post.id}",
        "title": post.title,
        "body": post.body,
        "tags": json.loads(post.tags_json or "[]"),
        "author": name,
        "initials": "✓" if official else _initials(name),
        "time": _relative(post.created_at),
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "votes": scores[("post", post.id)] + (post.seed_score or 0),
        "my_vote": mine.get(("post", post.id), 0),
        "answers": [a for a in (build(c) for c in children[None]) if a is not None],
        "edited": post.edited_at is not None,
        "verified": bool(post.verified),
        "is_official": official,
        "is_mine": post.author_id == me.id,
    }


def _load_post(db, post_id: int) -> models.CommunityPost:
    post = db.query(models.CommunityPost).filter(models.CommunityPost.id == post_id, models.CommunityPost.deleted_at.is_(None)).first()
    if not post:
        raise HTTPException(status_code=404, detail="That question no longer exists.")
    return post


def _post_response(db, post_id: int, me: models.User) -> dict:
    db.expire_all()
    scores, mine = _vote_maps(db, me.id)
    return _serialize_post(_load_post(db, post_id), me, scores, mine)


@router.get("/posts", summary="List community questions with their full reply threads")
def list_posts(me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        posts = (
            db.query(models.CommunityPost)
            .filter(models.CommunityPost.deleted_at.is_(None))
            .order_by(models.CommunityPost.created_at.desc())
            .all()
        )
        scores, mine = _vote_maps(db, me.id)
        return {"posts": [_serialize_post(p, me, scores, mine) for p in posts]}
    finally:
        db.close()


class SimilarRequest(BaseModel):
    title: str = ""
    body: str = ""


@router.post("/similar", summary="Existing questions that look like a draft (shown while writing a post)")
def similar(req: SimilarRequest, me: models.User = Depends(get_current_user)):
    from app.community_similar import similar_posts

    if len(req.title.strip()) + len(req.body.strip()) < 10:
        return {"similar": []}
    db = SessionLocal()
    try:
        return {"similar": similar_posts(db, req.title[:MAX_TITLE], req.body[:MAX_BODY])}
    finally:
        db.close()


@router.post("/posts", summary="Ask a question")
def create_post(req: PostCreate, me: models.User = Depends(get_current_user)):
    title = _clean(req.title, MAX_TITLE, "Title")
    body = _clean(req.body, MAX_BODY, "Details")
    tags = [t.strip()[:30] for t in req.tags if t.strip()][:MAX_TAGS]
    db = SessionLocal()
    try:
        _ensure_can_write(db, me)
        _moderate(db, me, title, body)
        post = models.CommunityPost(author_id=me.id, title=title, body=body, tags_json=json.dumps(tags))
        db.add(post)
        db.commit()
        return _post_response(db, post.id, me)
    finally:
        db.close()


@router.put("/posts/{post_id}", summary="Edit your own question")
def edit_post(post_id: str, req: PostEdit, me: models.User = Depends(get_current_user)):
    pid = _parse_id(post_id, "p")
    title = _clean(req.title, MAX_TITLE, "Title")
    body = _clean(req.body, MAX_BODY, "Details")
    db = SessionLocal()
    try:
        _ensure_can_write(db, me)
        post = _load_post(db, pid)
        if post.author_id != me.id:
            raise HTTPException(status_code=403, detail="You can only edit your own questions.")
        _moderate(db, me, title, body)
        post.title, post.body, post.edited_at = title, body, datetime.datetime.utcnow()
        db.commit()
        return _post_response(db, pid, me)
    finally:
        db.close()


@router.delete("/posts/{post_id}", summary="Delete your own question")
def delete_post(post_id: str, me: models.User = Depends(get_current_user)):
    pid = _parse_id(post_id, "p")
    db = SessionLocal()
    try:
        post = _load_post(db, pid)
        if post.author_id != me.id:
            raise HTTPException(status_code=403, detail="You can only delete your own questions.")
        # Soft delete: hidden from everyone, kept for moderation history.
        post.deleted_at, post.deleted_by, post.delete_reason = datetime.datetime.utcnow(), me.id, "Deleted by author"
        db.commit()
        return {"status": "deleted", "id": post_id}
    finally:
        db.close()


@router.post("/posts/{post_id}/comments", summary="Answer a question, or reply to any answer/reply")
def add_comment(post_id: str, req: CommentCreate, me: models.User = Depends(get_current_user)):
    pid = _parse_id(post_id, "p")
    body = _clean(req.body, MAX_BODY, "Reply")
    db = SessionLocal()
    try:
        _ensure_can_write(db, me)
        _load_post(db, pid)
        parent_id = None
        if req.parent_id:
            parent_id = _parse_id(req.parent_id, "c")
            parent = db.query(models.CommunityComment).filter(models.CommunityComment.id == parent_id).first()
            if not parent or parent.post_id != pid or parent.deleted_at:
                raise HTTPException(status_code=404, detail="The reply you're answering no longer exists.")
        _moderate(db, me, "", body)
        db.add(models.CommunityComment(post_id=pid, parent_id=parent_id, author_id=me.id, body=body, is_official=me.role == "admin"))
        db.commit()
        return _post_response(db, pid, me)
    finally:
        db.close()


def _own_comment(db, comment_id: str, me: models.User) -> models.CommunityComment:
    cid = _parse_id(comment_id, "c")
    c = db.query(models.CommunityComment).filter(models.CommunityComment.id == cid, models.CommunityComment.deleted_at.is_(None)).first()
    if not c:
        raise HTTPException(status_code=404, detail="That reply no longer exists.")
    if c.author_id != me.id:
        raise HTTPException(status_code=403, detail="You can only change your own replies.")
    return c


@router.put("/comments/{comment_id}", summary="Edit your own answer or reply")
def edit_comment(comment_id: str, req: CommentEdit, me: models.User = Depends(get_current_user)):
    body = _clean(req.body, MAX_BODY, "Reply")
    db = SessionLocal()
    try:
        _ensure_can_write(db, me)
        c = _own_comment(db, comment_id, me)
        _moderate(db, me, "", body)
        c.body, c.edited_at = body, datetime.datetime.utcnow()
        db.commit()
        return _post_response(db, c.post_id, me)
    finally:
        db.close()


@router.delete("/comments/{comment_id}", summary="Delete your own answer or reply")
def delete_comment(comment_id: str, me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        c = _own_comment(db, comment_id, me)
        c.deleted_at, c.deleted_by, c.delete_reason = datetime.datetime.utcnow(), me.id, "Deleted by author"
        db.commit()
        return _post_response(db, c.post_id, me)
    finally:
        db.close()


@router.post("/vote", summary="Upvote (1), downvote (-1) or clear (0) a question, answer or reply")
def vote(req: VoteRequest, me: models.User = Depends(get_current_user)):
    if req.value not in (1, -1, 0):
        raise HTTPException(status_code=400, detail="Vote must be 1, -1 or 0.")
    target_type = "post" if req.target.startswith("p-") else "comment"
    tid = _parse_id(req.target, "p" if target_type == "post" else "c")
    db = SessionLocal()
    try:
        _ensure_can_write(db, me)
        model = models.CommunityPost if target_type == "post" else models.CommunityComment
        target = db.query(model).filter(model.id == tid, model.deleted_at.is_(None)).first()
        if not target:
            raise HTTPException(status_code=404, detail="That item no longer exists.")
        existing = (
            db.query(models.CommunityVote)
            .filter_by(user_id=me.id, target_type=target_type, target_id=tid)
            .first()
        )
        if req.value == 0:
            if existing:
                db.delete(existing)
        elif existing:
            existing.value = req.value
        else:
            db.add(models.CommunityVote(user_id=me.id, target_type=target_type, target_id=tid, value=req.value))
        db.commit()
        if target_type == "post" and req.value == 1:
            from app.community_knowledge import maybe_add_popular

            maybe_add_popular(db, target)
        score = (
            db.query(func.coalesce(func.sum(models.CommunityVote.value), 0))
            .filter_by(target_type=target_type, target_id=tid)
            .scalar()
        )
        return {"target": req.target, "votes": int(score) + (target.seed_score or 0), "my_vote": req.value}
    finally:
        db.close()
