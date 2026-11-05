import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.demo_community import DEMO_POSTS
from app.seed import _seed_demo_community


def test_demo_questions_are_added_once_and_deleted_ones_stay_deleted(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'seed.db'}")
    models.Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    demo = lambda: db.query(models.CommunityPost).filter(models.CommunityPost.author_id.is_(None))

    _seed_demo_community(db)
    assert demo().count() == len(DEMO_POSTS)
    assert db.query(models.CommunityComment).count() > 0

    # A restart adds nothing more, and a post an admin deleted isn't brought back
    first = demo().first()
    first.deleted_at = datetime.datetime.utcnow()
    db.commit()
    _seed_demo_community(db)
    assert demo().count() == len(DEMO_POSTS)
    assert demo().filter(models.CommunityPost.deleted_at.is_(None)).count() == len(DEMO_POSTS) - 1

    # One missing from an earlier, partial seed is added
    missing = demo().filter(models.CommunityPost.title == DEMO_POSTS[-1]["title"]).one()
    db.query(models.CommunityComment).filter(models.CommunityComment.post_id == missing.id).delete()
    db.delete(missing)
    db.commit()
    _seed_demo_community(db)
    assert demo().filter(models.CommunityPost.title == DEMO_POSTS[-1]["title"]).count() == 1
