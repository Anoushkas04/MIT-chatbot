"""Regression tests: sources only when an answer actually relies on them."""
import re
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.multilingual as ml
import app.routers.chat_router as chat_router
from app import models
from app.citations import select_citations
from app.conversational import small_talk_kind
from app.providers.base import GenerationResult
from app.schemas import ChatRequest


class Student:
    id, role = "student-1", "student"


@pytest.fixture
def chat(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'chat.db'}")
    models.Base.metadata.create_all(engine)
    monkeypatch.setattr(chat_router, "SessionLocal", sessionmaker(bind=engine))
    monkeypatch.setattr(ml, "complete_text", lambda *a: None)  # local mode

    def ask(message):
        return chat_router.chat_query(ChatRequest(message=message, session_id=uuid.uuid4().hex[:30]), me=Student())

    return ask


@pytest.mark.parametrize("message", ["Hi", "Hello, how are you?", "Thank you", "thanks a lot!", "ok got it", "bye", "what can you do?"])
def test_small_talk_gets_a_conversational_reply_without_retrieval_or_sources(chat, monkeypatch, message):
    def no_retrieval(*args, **kwargs):
        raise AssertionError("small talk must not search the documents")

    for name in ("hybrid_search", "calendar_evidence", "club_evidence", "lookup_faculty", "generate_answer"):
        monkeypatch.setattr(chat_router, name, no_retrieval)
    reply = chat(message)
    assert reply.confidence == "conversational"
    assert reply.citations == [] and reply.sources == [] and not re.search(r"\[E\d+\]", reply.text)
    assert reply.text.strip()


def test_small_talk_with_a_real_question_still_searches():
    assert small_talk_kind("hi, when is REVELS?") is None
    assert small_talk_kind("thanks! and what is the fee for CSE") is None
    assert small_talk_kind("नमस्ते") == "greeting"


def test_attendance_question_cites_only_supporting_policy_documents(chat):
    reply = chat("What is the attendance requirement?")
    assert reply.citations, "a factual answer must have sources"
    allowed = {"Regulations 2026 B.Tech.pdf", "MIT - UG - Hand Book-- 2024 - Revised.pdf"}
    assert set(reply.sources) <= allowed
    markers = {int(n) for n in re.findall(r"\[E(\d+)\]", reply.text)}
    assert markers == {c.index for c in reply.citations}  # every source is cited in the text, numbered 1..n
    assert sorted(markers) == list(range(1, len(markers) + 1))


def test_cse_professors_cite_the_faculty_directory(chat):
    reply = chat("Who are the CSE professors?")
    assert [c.kind for c in reply.citations] == ["faculty"]
    assert "School of Computer Engineering" in reply.text


def test_unanswerable_question_gets_an_honest_reply_and_no_sources(chat):
    reply = chat("What is the wifi password for the hostel blocks?")
    assert reply.citations == [] and reply.sources == []
    assert "couldn't find" in reply.text.lower()


def test_two_part_question_cites_only_relevant_documents(chat):
    reply = chat("What is the minimum attendance and when do end semester exams start?")
    relevant = {"Academic Calendar 26-27 (1).pdf", "MIT_Manipal_Academic_Calendar_2026-27.md",
                "Regulations 2026 B.Tech.pdf", "MIT - UG - Hand Book-- 2024 - Revised.pdf"}
    assert reply.citations and set(reply.sources) <= relevant


def test_a_model_answer_using_two_documents_cites_both_and_drops_the_unrelated_one(chat, monkeypatch):
    evidence = [
        {"source_file": "MIT - UG - Hand Book-- 2024 - Revised.pdf", "text": "Only students with a minimum attendance of 75% may write the end semester examination.", "score": 1.0, "source_type": "official"},
        {"source_file": "BTech_ECE_Syllabus_2018.pdf", "text": "Digital signal processing laboratory experiments and filter design.", "score": 0.9, "source_type": "official"},
        {"source_file": "Academic Calendar 26-27 (1).pdf", "text": "End Semester Exams start on 2026-11-14 and end on 2026-11-28.", "score": 0.8, "source_type": "official"},
    ]
    monkeypatch.setattr(chat_router, "hybrid_search", lambda *a, **k: evidence)
    monkeypatch.setattr(chat_router, "calendar_evidence", lambda q: [])

    def model(request):
        # Like a real model: markers follow the order the passages were given in, and it also
        # (wrongly) cites the unrelated syllabus on the first claim
        n = {e["source_file"]: i for i, e in enumerate(request.evidence, start=1)}
        handbook, calendar = n["MIT - UG - Hand Book-- 2024 - Revised.pdf"], n["Academic Calendar 26-27 (1).pdf"]
        # The relevance filter may already have dropped the syllabus; if not, cite it anyway
        ece = f"[E{n['BTech_ECE_Syllabus_2018.pdf']}]" if "BTech_ECE_Syllabus_2018.pdf" in n else "[E9]"
        return GenerationResult(
            f"You need a minimum attendance of 75% to write the end semester examination [E{handbook}]{ece}. "
            f"End semester exams start on 2026-11-14 [E{calendar}].", "gemini", "test")

    monkeypatch.setattr(chat_router, "generate_answer", model)
    reply = chat("What is the minimum attendance and when do end semester exams start?")
    assert reply.sources == ["MIT - UG - Hand Book-- 2024 - Revised.pdf", "Academic Calendar 26-27 (1).pdf"]
    assert reply.text.count("[E1]") == 1 and reply.text.count("[E2]") == 1 and "[E3]" not in reply.text  # renumbered


def test_unsupported_markers_are_removed_and_the_rest_renumbered():
    evidence = [
        {"text": "Quantum computing electives."},
        {"text": "A student with less than 75% attendance is not permitted to write the end semester examination."},
    ]
    text, cited = select_citations("Students need 75% attendance for the end semester examination [E1][E2].", evidence, "attendance requirement")
    assert text == "Students need 75% attendance for the end semester examination [E1]."
    assert [(n, e["text"][:9]) for n, e in cited] == [(1, "A student")]
    assert select_citations("No markers here.", evidence, "attendance")[1] == []
