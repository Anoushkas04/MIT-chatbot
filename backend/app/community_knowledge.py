"""Community posts as chatbot knowledge.

A post enters the chatbot's knowledge ("the dataset") when an admin verifies it, or
automatically once it has POPULAR_THRESHOLD upvotes from distinct accounts. Popular
posts are NOT verified: the chatbot cites them as popular community answers, and only
admin-verified posts carry the verified label.

Posts are searched live from the database at question time, so later answers, edits
and deletions are reflected immediately without re-indexing.
"""
import re
from typing import Optional

from app import audit, models

POPULAR_THRESHOLD = 50

_STOPWORDS = {"the", "and", "for", "are", "how", "what", "when", "where", "who", "why", "can", "does", "with", "about", "this", "that", "have", "from", "you", "your"}


def upvote_count(db, post_id: int) -> int:
    """Distinct accounts that currently upvote the post (seeded demo scores don't count)."""
    return (
        db.query(models.CommunityVote)
        .filter_by(target_type="post", target_id=post_id, value=1)
        .count()
    )


def dataset_source(post: models.CommunityPost) -> Optional[str]:
    if not post.in_dataset:
        return None
    return "community_verified" if post.verified else "community_popular"


def maybe_add_popular(db, post: models.CommunityPost) -> bool:
    """Adds the post to the chatbot dataset once it crosses the upvote threshold."""
    if post.in_dataset or post.deleted_at:
        return False
    count = upvote_count(db, post.id)
    if count < POPULAR_THRESHOLD:
        return False
    post.in_dataset = True
    audit.record(
        db,
        None,
        "dataset.community_popular",
        f'Added "{post.title}" to the chatbot dataset automatically ({count} upvotes).',
        "post",
        f"p-{post.id}",
        {"upvotes": count, "threshold": POPULAR_THRESHOLD},
    )
    db.commit()
    return True


def _visible_answers(post: models.CommunityPost, scores: dict) -> list:
    answers = [c for c in post.comments if c.deleted_at is None]
    # Official replies first, then the community's best-voted answers.
    return sorted(answers, key=lambda c: (not c.is_official, -scores.get(c.id, 0)))


def knowledge_text(post: models.CommunityPost, scores: dict) -> str:
    label = "verified by the MITra team" if post.verified else "popular community answer, not officially verified"
    lines = [f'Community question ({label}): "{post.title.strip()}"', f"Question context: {post.body.strip()}"]
    answers = _visible_answers(post, scores)[:4]
    if answers:
        lines.append("Answers:")
        for c in answers:
            who = "MITra Official" if c.is_official else "Student"
            lines.append(f' • {who}: "{c.body.strip()}"')
    return "\n".join(lines)


def search_dataset_posts(user_query: str, db, limit: int = 3) -> list:
    """Chat retrieval over community posts that are in the dataset (verified first)."""
    words = [w for w in re.findall(r"\b\w+\b", user_query.lower()) if len(w) >= 3 and w not in _STOPWORDS]
    if not words:
        return []
    posts = (
        db.query(models.CommunityPost)
        .filter(models.CommunityPost.in_dataset.is_(True), models.CommunityPost.deleted_at.is_(None))
        .all()
    )
    if not posts:
        return []
    score_rows = (
        db.query(models.CommunityVote.target_id, models.CommunityVote.value)
        .filter(models.CommunityVote.target_type == "comment")
        .all()
    )
    comment_scores: dict = {}
    for tid, value in score_rows:
        comment_scores[tid] = comment_scores.get(tid, 0) + value

    results = []
    for p in posts:
        text = knowledge_text(p, comment_scores)
        matched = sum(1 for w in words if w in text.lower())
        if not matched:
            continue
        score = min(0.98, 0.75 + matched * 0.08 + (0.1 if p.verified else 0))
        results.append({
            "source": f"MITra Community{' (verified)' if p.verified else ''}: '{p.title.strip()}'",
            "source_type": "community_verified" if p.verified else "community",
            "text": text,
            "score": round(score, 2),
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def notify(db, user_id: Optional[str], title: str, content: str, category: str, icon: str = "📢") -> None:
    """In-app notification to a student (no-op for seeded posts without an account)."""
    if not user_id:
        return
    db.add(models.Notification(user_id=user_id, icon=icon, title=title, content=content, category=category, type_color="blue"))
