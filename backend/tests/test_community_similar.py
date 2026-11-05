import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.community_similar import similar_posts
from app.demo_community import DEMO_POSTS


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'community.db'}")
    models.Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    for p in DEMO_POSTS:
        session.add(models.CommunityPost(author_label=p["author"], title=p["title"], body=p["body"]))
    session.commit()
    yield session
    session.close()


# Phrasings not used while choosing the thresholds
@pytest.mark.parametrize("draft, expected", [
    ("Are lab hours and theory hours counted together for the attendance percentage?", "75% attendance rule"),
    ("tips for the operating systems end sem apart from PYQs", "OS end-sem"),
    ("my hostel outpass request has been pending for 3 days", "hostel outpass"),
    ("IEEE vs robotics club, which one should a second year join?", "IEEE and Robotics"),
])
def test_rephrased_questions_find_the_existing_one(db, draft, expected):
    found = similar_posts(db, draft)
    assert found and expected.lower() in found[0]["title"].lower()


@pytest.mark.parametrize("draft", [
    "When does REVELS start this year?",
    "What is the tuition fee for B.Tech Mechanical?",
    "Is the AB5 canteen open on Sundays?",
    "How strict is attendance in the hostel mess?",  # one shared word isn't the same question
])
def test_different_questions_are_not_flagged(db, draft):
    assert similar_posts(db, draft) == []
