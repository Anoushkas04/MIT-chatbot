import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.routers.admin_dataset as admin_dataset
import app.routers.chat_router as chat_router
from app import models


@pytest.fixture
def db(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'feedback.db'}")
    models.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    monkeypatch.setattr(chat_router, "SessionLocal", Session)
    monkeypatch.setattr(admin_dataset, "SessionLocal", Session)
    s = Session()
    s.add_all([models.ChatSession(id="s1", user_id="me", role="student", title="q"),
               models.ChatSession(id="s2", user_id="other", role="student", title="q")])
    s.add_all([models.ChatMessage(id=1, session_id="s1", sender_role="user", text="when is revels", timestamp="Now"),
               models.ChatMessage(id=2, session_id="s1", sender_role="assistant", text="REVELS is 17-20 Feb [E1]", timestamp="Now"),
               models.ChatMessage(id=3, session_id="s2", sender_role="assistant", text="someone else's answer", timestamp="Now")])
    s.commit()
    return Session


class User:
    def __init__(self, uid):
        self.id = uid


def test_students_rate_their_own_answers_and_admins_see_the_summary(db):
    chat_router.answer_feedback(chat_router.AnswerFeedback(message_id=2, rating=-1), me=User("me"))
    summary = admin_dataset.answer_feedback_summary(admin=User("admin"))
    assert summary["not_helpful"] == 1 and summary["rate"] == 0.0
    assert summary["recent_not_helpful"][0]["question"] == "when is revels"
    chat_router.answer_feedback(chat_router.AnswerFeedback(message_id=2, rating=0), me=User("me"))  # cleared
    assert admin_dataset.answer_feedback_summary(admin=User("admin"))["rate"] is None


def test_other_students_answers_and_questions_cant_be_rated(db):
    for message_id in (3, 1):  # someone else's answer; a question, not an answer
        with pytest.raises(HTTPException) as err:
            chat_router.answer_feedback(chat_router.AnswerFeedback(message_id=message_id, rating=1), me=User("me"))
        assert err.value.status_code == 404


def test_quality_check_reports_ranking_metrics_and_compares_with_the_last_run(db):
    first = admin_dataset.evaluate(admin=User("admin"))
    assert first["previous"] is None
    assert 0 < first["retrieval"]["mrr"] <= 1 and 0 < first["retrieval"]["ndcg_at_5"] <= 1
    second = admin_dataset.evaluate(admin=User("admin"))
    assert second["previous"]["retrieval"]["mrr"] == first["retrieval"]["mrr"]
