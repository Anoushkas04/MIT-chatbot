from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import SessionLocal
from app import models

router = APIRouter(prefix="/api/posts", tags=["5. Student Community & Crowdsourcing"])


class PostCreateRequest(BaseModel):
    author_name: str
    sub_community: str = "Hostel & Mess"
    tag: str = "General"
    title: str
    content: str


class CommentCreateRequest(BaseModel):
    author_name: str
    content: str


# 11-Category Taxonomy
COMMUNITY_CATEGORIES = [
    "Academics",
    "Campus Life",
    "Hostels",
    "Mess",
    "Clubs",
    "Events",
    "Transportation",
    "Resources",
    "General",
    "Lost & Found",
    "Advice",
]


@router.get("", summary="Get student community posts filtered by category")
def get_posts(category: Optional[str] = None):
    db = SessionLocal()
    try:
        query = db.query(models.StudentPost).order_by(models.StudentPost.id.desc())
        
        if category and category.lower() != "all":
            cat_lower = category.lower()
            db_posts = query.all()
            filtered = [
                p for p in db_posts
                if (p.sub_community and cat_lower in p.sub_community.lower())
                or (p.tag and cat_lower in p.tag.lower())
            ]
        else:
            filtered = query.all()

        formatted_posts = [
            {
                "id": p.id,
                "author": p.author_name,
                "sub_community": p.sub_community or "General",
                "tag": p.tag or "General",
                "title": p.title,
                "content": p.content,
                "upvotes": p.upvotes,
                "downvotes": getattr(p, "downvotes", 0) or 0,
                "verified": p.verified,
                "time": p.time or "Just now",
                "comments": [
                    {
                        "id": c.id,
                        "author": c.author_name,
                        "content": c.content,
                        "is_helpful": getattr(c, "is_helpful", False),
                    }
                    for c in p.comments
                ] if p.comments else [],
            }
            for p in filtered
        ]

        return formatted_posts
    finally:
        db.close()


@router.post("", summary="Create a new student community post")
def create_post(req: PostCreateRequest):
    from app.category_validator import validate_post_category
    from app.moderation_engine import (
        check_user_suspension_status,
        evaluate_community_content,
        process_user_strike_and_suspension,
    )

    db = SessionLocal()
    try:
        # 1. Check User Account Suspension Status
        is_suspended, susp_msg, _ = check_user_suspension_status(db, req.author_name)
        if is_suspended:
            raise HTTPException(status_code=403, detail=susp_msg)

        # 2. Pre-Publish Prohibited Content Moderation Check
        is_prohibited, category, reason, confidence = evaluate_community_content(req.title, req.content)
        if is_prohibited and confidence >= 0.80:
            process_user_strike_and_suspension(
                db, None, req.author_name, category, f"{req.title}: {req.content}"
            )
            raise HTTPException(
                status_code=400,
                detail="⚠️ This post cannot be published because it violates the Student Community Guidelines. Repeated violations may result in temporary suspension of your account."
            )

        # 3. Category Mismatch Validation
        target_cat = req.sub_community or req.tag or "General"
        is_valid, cat_reason, confidence = validate_post_category(req.title, req.content, target_cat)
        if not is_valid and confidence >= 0.80:
            raise HTTPException(
                status_code=400,
                detail=f"Category Mismatch: The selected category '{target_cat}' does not appear to match your question. {cat_reason} Please choose a more appropriate category."
            )

        post = models.StudentPost(
            author_name=req.author_name,
            sub_community=req.sub_community or "General",
            tag=req.tag or "General",
            title=req.title,
            content=req.content,
            upvotes=1,
            downvotes=0,
            verified=False,
            time="Just now",
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        return {
            "id": post.id,
            "author": post.author_name,
            "sub_community": post.sub_community,
            "tag": post.tag,
            "title": post.title,
            "content": post.content,
            "upvotes": post.upvotes,
            "downvotes": post.downvotes,
            "verified": post.verified,
            "time": post.time,
            "comments": [],
        }
    finally:
        db.close()


@router.post("/{post_id}/upvote", summary="Upvote a student tip")
def upvote_post(post_id: int):
    db = SessionLocal()
    try:
        post = db.query(models.StudentPost).filter(models.StudentPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found.")
        post.upvotes += 1
        db.commit()
        return {"id": post.id, "upvotes": post.upvotes}
    finally:
        db.close()


@router.post("/{post_id}/downvote", summary="Downvote a post")
def downvote_post(post_id: int):
    db = SessionLocal()
    try:
        post = db.query(models.StudentPost).filter(models.StudentPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found.")
        post.downvotes = (getattr(post, "downvotes", 0) or 0) + 1
        db.commit()
        return {"id": post.id, "downvotes": post.downvotes}
    finally:
        db.close()


@router.post("/{post_id}/comments", summary="Add peer comment to a post")
def add_comment(post_id: int, req: CommentCreateRequest):
    db = SessionLocal()
    try:
        post = db.query(models.StudentPost).filter(models.StudentPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found.")
        comment = models.PostComment(
            post_id=post_id,
            author_name=req.author_name,
            content=req.content,
            is_helpful=False,
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return {"id": comment.id, "author": comment.author_name, "content": comment.content, "is_helpful": False}
    finally:
        db.close()


@router.post("/comments/{comment_id}/mark-helpful", summary="Mark comment response as Accepted/Helpful Answer")
def mark_comment_helpful(comment_id: int):
    db = SessionLocal()
    try:
        comment = db.query(models.PostComment).filter(models.PostComment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found.")
        comment.is_helpful = True
        db.commit()
        return {"id": comment_id, "is_helpful": True, "message": "Marked as Accepted Helpful Answer!"}
    finally:
        db.close()


@router.get("/leaderboard", summary="Get top campus student contributors leaderboard from database")
def get_leaderboard():
    db = SessionLocal()
    try:
        users = (
            db.query(models.User)
            .filter(models.User.role == "student")
            .order_by(models.User.rewards_points.desc())
            .limit(10)
            .all()
        )
        leaderboard = [
            {
                "rank": idx + 1,
                "name": u.name,
                "dept": f"{u.department or 'MIT'} ({u.academic_year or 'Student'})",
                "points": u.rewards_points or 0,
                "helpful_answers": 0,
                "badge": "🎓 Verified Student" if u.is_verified else "🎓 Member",
            }
            for idx, u in enumerate(users)
        ]
        return leaderboard
    finally:
        db.close()
