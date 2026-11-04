import datetime
import sys

# Standalone entrypoint (`python -m app.seed`) doesn't go through app.main, so it
# needs its own UTF-8 stdout guard for the checkmark/emoji in the seed log lines.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from app.config import SEED_DEMO_COMMUNITY
from app.database import SessionLocal, init_db
from app import models


def seed_database():
    """Creates any missing tables, then (only with SEED_DEMO_COMMUNITY=1) seeds labelled
    demo Community questions into an empty feed. No fake users or student records."""
    init_db()
    db = SessionLocal()

    try:
        # Opt-in demo content for the Community feed (SEED_DEMO_COMMUNITY=1 only). Added
        # alongside real posts, once: demo posts are the ones with a label and no account, so
        # a restart (or an admin deleting them, which keeps the row) never seeds them again.
        demo_seeded = db.query(models.CommunityPost).filter(
            models.CommunityPost.author_id.is_(None), models.CommunityPost.author_label.isnot(None)
        ).first()
        if SEED_DEMO_COMMUNITY and not demo_seeded:
            _seed_demo_community(db)

    finally:
        db.close()


def _seed_demo_community(db) -> None:
    import json
    from app.demo_community import DEMO_POSTS

    def add_comments(post_id: int, parent_id, items: list) -> None:
        for item in items:
            comment = models.CommunityComment(
                post_id=post_id,
                parent_id=parent_id,
                author_label=item["author"],
                body=item["body"],
                seed_score=item["votes"],
                created_at=datetime.datetime.utcnow() - datetime.timedelta(days=item["days_ago"]),
            )
            db.add(comment)
            db.flush()  # need comment.id before seeding its own replies
            add_comments(post_id, comment.id, item.get("replies", []))

    for p in DEMO_POSTS:
        post = models.CommunityPost(
            title=p["title"],
            body=p["body"],
            tags_json=json.dumps(p["tags"]),
            author_label=p["author"],
            seed_score=p["votes"],
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=p["days_ago"]),
        )
        db.add(post)
        db.flush()  # need post.id before seeding its answers
        add_comments(post.id, None, p.get("answers", []))

    db.commit()
    print(f"✓ Database Seeded: {len(DEMO_POSTS)} labelled demo Community questions (SEED_DEMO_COMMUNITY=1).")


if __name__ == "__main__":
    seed_database()
