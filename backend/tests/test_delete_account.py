import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import models
from app.routers.me_router import DeleteAccountRequest, delete_account, delete_user_data


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'accounts.db'}")
    # Enforce foreign keys like Postgres does, so a missed reference fails the test
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    models.Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _user(db, uid, role="student"):
    u = models.User(id=uid, email=f"{uid}@learner.manipal.edu", password_hash="x", name=uid.title(), role=role,
                    learner_id=f"L-{uid}")
    db.add(u)
    return u


def test_deleting_an_account_removes_personal_data_and_keeps_threads(db):
    _user(db, "asha")
    _user(db, "ravi")
    db.flush()
    chat = models.ChatSession(id="s1", user_id="asha")
    db.add(chat)
    db.flush()
    msg = models.ChatMessage(session_id="s1", sender_role="assistant", text="answer", timestamp="now")
    db.add(msg)
    db.flush()
    db.add(models.MessageCitation(message_id=msg.id, source_name="doc.pdf"))
    post = models.CommunityPost(author_id="asha", title="Hostel timings?", body="When do gates close?", tags_json="[]")
    db.add(post)
    db.flush()
    db.add(models.CommunityComment(post_id=post.id, author_id="ravi", body="10 pm"))
    db.add(models.CommunityComment(post_id=post.id, author_id="asha", body="Thanks!"))
    db.add(models.CommunityVote(user_id="asha", target_type="post", target_id=post.id, value=1))
    db.add(models.Notification(user_id="asha", title="Hi", content="Welcome"))
    db.add(models.SystemFeedback(user_id="asha", message="Nice app"))
    db.add(models.Connection(requester_id="asha", addressee_id="ravi"))
    db.add(models.DirectMessage(sender_id="ravi", recipient_id="asha", body="hey"))
    db.add(models.UserBlock(blocker_id="ravi", blocked_id="asha"))
    db.add(models.UserReport(reporter_id="ravi", reported_user_id="asha", reported_name="Asha", reason="spam"))
    db.add(models.UserReport(reporter_id="asha", reported_user_id="ravi", reported_name="Ravi", reason="spam"))
    db.add(models.AccountWarning(user_id="asha", text="Be kind", admin_id="admin"))
    suspension = models.Suspension(user_id="asha", source="admin", reason="spam")
    db.add(suspension)
    db.flush()
    db.add(models.Plea(suspension_id=suspension.id, user_id="asha", text="Please review my suspension."))
    db.add(models.AccountAppeal(user_id="asha", text="Please restore my account."))
    db.add(models.OTPRecord(learner_id="L-asha", otp_hash="h", expires_at=datetime.datetime.utcnow()))
    db.commit()

    delete_user_data(db, "asha")
    db.commit()

    assert db.query(models.User).filter_by(id="asha").first() is None
    assert db.query(models.User).filter_by(id="ravi").first() is not None
    for model in (models.ChatSession, models.ChatMessage, models.MessageCitation, models.CommunityVote,
                  models.Notification, models.Connection, models.DirectMessage, models.UserBlock,
                  models.AccountWarning, models.Suspension, models.Plea, models.AccountAppeal, models.OTPRecord):
        assert db.query(model).count() == 0, model.__name__
    # The thread stays: the question and Asha's reply lose their author, Ravi's reply is untouched
    kept = db.query(models.CommunityPost).one()
    assert kept.author_id is None and kept.author_label is None
    authors = sorted(str(c.author_id) for c in db.query(models.CommunityComment))
    assert authors == ["None", "ravi"]
    # The report about Asha stays for moderators without the link; the one she made is gone
    report = db.query(models.UserReport).one()
    assert report.reporter_id == "ravi" and report.reported_user_id is None
    assert db.query(models.SystemFeedback).one().user_id is None


def test_deletion_needs_the_typed_confirmation_and_is_not_for_admins():
    student = models.User(id="s", email="s@x", password_hash="x", name="S", role="student")
    with pytest.raises(HTTPException) as e:
        delete_account(DeleteAccountRequest(confirm="delete me"), student)
    assert e.value.status_code == 400
    admin = models.User(id="a", email="a@x", password_hash="x", name="A", role="admin")
    with pytest.raises(HTTPException) as e:
        delete_account(DeleteAccountRequest(confirm="DELETE"), admin)
    assert e.value.status_code == 403
