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
        # Opt-in demo content for the Community feed (SEED_DEMO_COMMUNITY=1 only), added
        # alongside real posts.
        if SEED_DEMO_COMMUNITY:
            _seed_demo_community(db)

    finally:
        db.close()


def _seed_demo_community(db) -> None:
    """Adds each demo question that isn't there yet. Demo posts are the ones with a label and
    no account; one an admin deleted keeps its row, so it isn't added again on restart."""
    import json
    from app.demo_community import DEMO_POSTS

    existing = {
        title
        for (title,) in db.query(models.CommunityPost.title).filter(
            models.CommunityPost.author_id.is_(None), models.CommunityPost.author_label.isnot(None)
        )
    }
    missing = [p for p in DEMO_POSTS if p["title"] not in existing]
    if not missing:
        return

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

    for p in missing:
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
    print(f"✓ Database Seeded: {len(missing)} labelled demo Community questions (SEED_DEMO_COMMUNITY=1).")


if __name__ == "__main__":
    seed_database()
