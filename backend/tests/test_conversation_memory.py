import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.routers.chat_router as chat_router
import app.session_memory as memory
from app import models
from app.schemas import ChatRequest


class Student:
    id, role = "student-1", "student"


def test_a_conversation_keeps_its_context_after_a_server_restart(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'chat.db'}")
    models.Base.metadata.create_all(engine)
    monkeypatch.setattr(chat_router, "SessionLocal", sessionmaker(bind=engine))
    monkeypatch.setattr(chat_router, "complete_text", lambda *a: None, raising=False)
    import app.multilingual as ml
    monkeypatch.setattr(ml, "complete_text", lambda *a: None)  # local mode: no model rewrite

    session = uuid.uuid4().hex[:30]
    chat_router.chat_query(ChatRequest(message="tell me about the astronomy club", session_id=session), me=Student())
    memory._sessions.clear()  # what a restart or the free instance sleeping does

    reply = chat_router.chat_query(ChatRequest(message="how do I contact them?", session_id=session), me=Student())
    assert reply.searched_for and "astronomy club" in reply.searched_for.lower()  # the earlier question came back
    assert len(memory.get_history(session)) == 4  # both turns are back in memory
