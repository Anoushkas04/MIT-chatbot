from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.answer_verifier import NO_EVIDENCE_MESSAGE, verify_answer
from app.providers.base import GenerationRequest, GenerationResult, evidence_text
from app.providers.local_provider import LocalProvider
from app.schemas import ChatRequest


class _Query:
    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return []

    def first(self):
        return None


class _Database:
    def query(self, *args, **kwargs):
        return _Query()

    def add(self, *args, **kwargs):
        return None

    def commit(self):
        return None

    def rollback(self):
        return None

    def flush(self):
        return None

    def close(self):
        return None


@pytest.fixture
def chat_router(monkeypatch):
    import app.routers.chat_router as chat_router

    monkeypatch.setattr(chat_router, "SessionLocal", _Database)
    return chat_router


def _official_evidence(**overrides):
    value = {
        "id": "policy-p2-c1",
        "document_id": "policy 2024",
        "source": "policy.pdf",
        "page_number": 2,
        "text": "Students require at least 75 percent attendance to write the examination.",
        "score": 0.92,
        "retrieval_method": "bm25+dense",
        "source_type": "official",
    }
    value.update(overrides)
    return value


def test_chat_contract_returns_grounded_answer_and_page_citation(chat_router, monkeypatch):
    router = chat_router
    monkeypatch.setattr(router, "hybrid_search", lambda *args, **kwargs: [_official_evidence()])
    monkeypatch.setattr(
        router,
        "generate_answer",
        lambda request: GenerationResult("The minimum is 75 percent [E1].", "local", "test"),
    )

    response = router.chat_query(ChatRequest(
        message=" What attendance is required? ",
        session_id=" edge-api-1 ",
    ))

    body = response.model_dump()
    assert body["text"] == "The minimum is 75 percent [E1]."
    assert body["provider"] == "local"
    assert body["sources"] == ["policy.pdf"]
    assert body["citations"][0]["page_number"] == 2
    assert body["citations"][0]["source_url"] == "/api/search/page/policy%202024/2"
    assert body["verification_warnings"] == []


def test_chat_contract_returns_explicit_no_evidence_response(chat_router, monkeypatch):
    router = chat_router
    monkeypatch.setattr(router, "hybrid_search", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        router,
        "generate_answer",
        lambda request: GenerationResult("unsupported guess", "local", "test"),
    )

    response = router.chat_query(ChatRequest(
        message="What is the teleportation portal policy?",
        session_id="edge-api-2",
    ))

    body = response.model_dump()
    assert "couldn't find reliable information" in body["text"]
    assert body["confidence"] == "no_evidence"
    assert body["citations"] == []
    assert body["sources"] == []


def test_chat_contract_degrades_safely_when_retrieval_raises(chat_router, monkeypatch):
    router = chat_router

    def fail_retrieval(*args, **kwargs):
        raise RuntimeError("index unavailable")

    monkeypatch.setattr(router, "hybrid_search", fail_retrieval)
    monkeypatch.setattr(
        router,
        "generate_answer",
        lambda request: GenerationResult(NO_EVIDENCE_MESSAGE, "local", "test"),
    )
    response = router.chat_query(ChatRequest(
        message="What is the attendance rule?",
        session_id="edge-api-3",
    ))

    assert response.confidence == "no_evidence"
    assert response.citations == []


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"message": "   ", "session_id": "valid"}, "message"),
        ({"message": "valid", "session_id": "   "}, "session_id"),
        ({"message": "x" * 4001, "session_id": "valid"}, "message"),
        ({"message": "valid", "session_id": "x" * 129}, "session_id"),
    ],
)
def test_chat_schema_rejects_invalid_or_oversized_input(payload, field):
    with pytest.raises(ValidationError) as caught:
        ChatRequest.model_validate(payload)
    assert any(item["loc"][-1] == field for item in caught.value.errors())


def test_chat_schema_requires_message_and_session_id():
    with pytest.raises(ValidationError) as caught:
        ChatRequest.model_validate({})
    locations = {item["loc"][-1] for item in caught.value.errors()}
    assert locations == {"message", "session_id"}


def test_chat_contract_removes_out_of_range_provider_citation(chat_router, monkeypatch):
    router = chat_router
    monkeypatch.setattr(router, "hybrid_search", lambda *args, **kwargs: [_official_evidence()])
    monkeypatch.setattr(
        router,
        "generate_answer",
        lambda request: GenerationResult("Supported [E1], invented [E9].", "local", "test"),
    )
    response = router.chat_query(ChatRequest(
        message="What attendance is required?",
        session_id="edge-api-4",
    ))

    assert "[E1]" in response.text
    assert "[E9]" not in response.text
    assert "invalid_citation_markers_removed" in response.verification_warnings


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("What is the attendance policy?", "academic_official"),
        ("Which hostel mess has the best food?", "community_experience"),
        ("What do students say about exam fees?", "academic_official"),
        ("Hello there", "academic_official"),
    ],
)
def test_intent_classification_edge_cases(question, expected):
    from app.routers.chat_router import classify_intent

    assert classify_intent(question) == expected


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("How to apply for an internship?", "procedural"),
        ("Compare CSE versus IT", "comparison"),
        ("Why is attendance required?", "explanation"),
        ("Who is the HOD?", "simple_factual"),
        ("Explain every relevant rule and implication in this unusually detailed multi part academic request today", "explanation"),
    ],
)
def test_query_type_classification_precedence(question, expected):
    from app.routers.chat_router import detect_query_type

    assert detect_query_type(question) == expected


def test_query_feature_extraction_prioritizes_urgent_signal():
    from app.routers.chat_router import extract_query_features

    features = extract_query_features(
        "Urgent: my scholarship payment deadline is today",
        "academic_official",
        "simple_factual",
        "low",
        "official",
    )
    assert features["sentiment"] == "Urgent"
    assert features["topic"] == "Fees & Finance"


def test_relevance_filter_handles_only_stopwords_and_does_not_mutate_input():
    from app.routers.chat_router import filter_chunk_relevance

    records = [
        {"id": str(index), "text": f"record {index}", "score": 0.4}
        for index in range(5)
    ]
    snapshot = [dict(record) for record in records]
    result = filter_chunk_relevance(records, "what is the official information", "simple_factual")

    assert len(result) == 3
    assert records == snapshot


def test_relevance_filter_penalizes_bibliography_for_non_book_question():
    from app.routers.chat_router import filter_chunk_relevance

    results = filter_chunk_relevance([
        {"id": "reference", "text": "Attendance references: ISBN publisher", "score": 0.9},
        {"id": "rule", "text": "Attendance below 75 percent is insufficient", "score": 0.7},
    ], "attendance requirement", "simple_factual")

    assert results[0]["id"] == "rule"
    assert results[1]["score"] < 0.6


@pytest.mark.parametrize(
    ("score", "expected"),
    [(0.75, "high"), (0.35, "medium"), (0.01, "low"), (0.0, "no_evidence")],
)
def test_confidence_threshold_boundaries(score, expected):
    from app.hallucination_guard import evaluate_confidence

    confidence, _, _ = evaluate_confidence([{"score": score, "source_type": "official"}])
    assert confidence == expected


def test_community_confidence_is_labeled_separately():
    from app.hallucination_guard import evaluate_confidence

    _, confidence_type, _ = evaluate_confidence([{"score": 0.8, "source_type": "community"}])
    assert confidence_type == "community_grounded"


def test_answer_verifier_rejects_whitespace_provider_response():
    answer, warnings = verify_answer("   ", [_official_evidence()])
    assert answer == NO_EVIDENCE_MESSAGE
    assert warnings == ["empty_provider_response"]


def test_answer_verifier_warns_when_provider_omits_markers():
    answer, warnings = verify_answer("The minimum attendance is 75 percent.", [_official_evidence()])
    assert answer.endswith("75 percent.")
    assert warnings == ["provider_omitted_inline_citations"]


def test_answer_verifier_normalizes_grouped_provider_markers():
    answer, warnings = verify_answer(
        "The policy is supported by both sources [E1, E2].",
        [_official_evidence(), _official_evidence(id="policy-p3-c1")],
    )

    assert answer == "The policy is supported by both sources [E1] [E2]."
    assert warnings == []


def test_local_provider_never_emits_marker_outside_evidence_range():
    request = GenerationRequest(
        question="What attendance is required?",
        system_prompt="",
        evidence=[_official_evidence(), _official_evidence(id="other", text="Exams begin in May 2026.")],
    )
    text = LocalProvider().generate(request).text
    assert "[E1]" in text
    assert "[E3]" not in text


def test_evidence_prompt_limits_history_and_numbers_each_source():
    request = GenerationRequest(
        question="What is the rule?",
        system_prompt="",
        evidence=[_official_evidence(), _official_evidence(source="second.pdf", page_number=3)],
        history=[{"role": "user", "text": f"turn-{index}"} for index in range(8)],
    )
    prompt = evidence_text(request)
    assert "turn-0" not in prompt
    assert "turn-1" not in prompt
    assert "turn-2" in prompt
    assert "[E1: policy.pdf, page 2]" in prompt
    assert "[E2: second.pdf, page 3]" in prompt


def test_session_memory_is_isolated_and_capped(monkeypatch):
    import app.session_memory as memory

    memory._sessions.clear()
    monkeypatch.setattr(memory, "MAX_HISTORY_TURNS", 2)
    for index in range(3):
        memory.add_turn("one", f"question-{index}", f"answer-{index}")
    memory.add_turn("two", "other-question", "other-answer")

    assert len(memory.get_history("one")) == 4
    assert memory.get_history("one")[0]["text"] == "question-1"
    assert len(memory.get_history("two")) == 2


def test_hybrid_search_returns_empty_for_blank_query_without_loading_stores(monkeypatch):
    import app.rag.hybrid as hybrid

    monkeypatch.setattr(
        hybrid,
        "get_store",
        lambda: (_ for _ in ()).throw(AssertionError("store should not load")),
    )
    assert hybrid.hybrid_search("   ") == []
    assert hybrid.hybrid_search("attendance", final_k=0) == []


def test_hybrid_search_survives_all_retriever_failures(monkeypatch):
    import app.rag.hybrid as hybrid

    broken = SimpleNamespace(search=lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline")))
    monkeypatch.setattr(hybrid, "get_store", lambda: broken)
    monkeypatch.setattr(hybrid, "get_keyword_store", lambda: broken)
    monkeypatch.setattr(hybrid, "get_visual_store", lambda: broken)
    monkeypatch.setattr(hybrid, "embed_query", lambda query: [0.0])
    monkeypatch.setattr(hybrid, "VISUAL_RAG_ENABLED", True)

    assert hybrid.hybrid_search("attendance") == []


def test_hybrid_search_fuses_duplicate_hits_and_reports_methods(monkeypatch):
    import app.rag.hybrid as hybrid

    hit = _official_evidence()
    store = SimpleNamespace(search=lambda *args, **kwargs: [hit])
    monkeypatch.setattr(hybrid, "get_store", lambda: store)
    monkeypatch.setattr(hybrid, "get_keyword_store", lambda: store)
    monkeypatch.setattr(hybrid, "embed_query", lambda query: [0.0])
    monkeypatch.setattr(hybrid, "VISUAL_RAG_ENABLED", False)

    result = hybrid.hybrid_search("attendance", final_k=4)
    assert len(result) == 1
    assert result[0]["retrieval_method"] == "bm25+dense"


def test_provider_registry_falls_back_when_remote_returns_empty(monkeypatch):
    import app.providers.registry as registry

    class EmptyProvider:
        name = "gemini"

        def generate(self, request):
            return GenerationResult("", self.name, "empty-model")

    monkeypatch.setattr(registry, "get_provider", lambda: EmptyProvider())
    result = registry.generate_answer(GenerationRequest(
        question="What attendance is required?",
        system_prompt="",
        evidence=[_official_evidence()],
    ))
    assert result.provider == "local"
    assert "[E1]" in result.text


def test_source_merge_honors_zero_limit():
    from app.routers.chat_router import merge_evidence

    assert merge_evidence([_official_evidence()], [], prefer_community=False, limit=0) == []


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("list professors in CSE department", "School of Computer Engineering"),
        ("show faculty in electronics and communication", "School of Electrical Engineering"),
        ("list teachers in mechatronics", "School of Mechanical Engineering"),
        ("faculty in chemical engineering", "School of Civil & Chemical Engineering"),
        ("professors in mathematics", "School of Basic Sciences, Humanities & Management"),
    ],
)
def test_faculty_department_aliases(query, expected):
    from app.faculty_directory import detect_department

    assert detect_department(query) == expected


def test_faculty_department_query_returns_complete_source_backed_list():
    from app.faculty_directory import lookup_faculty

    result = lookup_faculty("list professors in computer science department")

    assert result is not None
    assert result["kind"] == "department_list"
    assert len(result["records"]) == 180
    assert "School of Computer Engineering has 180 faculty records" in result["answer"]
    assert "Dr. Radhika M Pai" in result["answer"]
    assert result["evidence"]["retrieval_method"] == "structured_faculty_directory"


@pytest.mark.parametrize(
    "query",
    [
        "tell me about Radhika Pai",
        "tell me about Dr. Radhika Pai",
        "what is Radhika Pai's cabin?",
    ],
)
def test_faculty_person_lookup_does_not_require_honorific(query):
    from app.faculty_directory import lookup_faculty

    result = lookup_faculty(query)

    assert result is not None
    assert result["kind"] == "person"
    assert len(result["records"]) == 1
    assert result["records"][0]["name"] == "Dr. Radhika M Pai"
    assert "Faculty Rooms 8 SCE/FC 74" in result["answer"]


def test_unrelated_tell_me_about_query_does_not_trigger_faculty_lookup():
    from app.faculty_directory import lookup_faculty

    assert lookup_faculty("tell me about the attendance requirement") is None


def test_chat_contract_uses_structured_faculty_answer_without_llm(chat_router, monkeypatch):
    router = chat_router
    monkeypatch.setattr(
        router,
        "hybrid_search",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("general RAG should be skipped")),
    )
    monkeypatch.setattr(
        router,
        "generate_answer",
        lambda request: (_ for _ in ()).throw(AssertionError("LLM should be skipped")),
    )

    response = router.chat_query(ChatRequest(
        message="tell me about Radhika Pai",
        session_id="faculty-edge-1",
    ))

    assert response.provider == "local"
    assert response.model == "structured-faculty-directory-v1"
    assert response.confidence == "high"
    assert len(response.citations) == 1
    assert response.citations[0].retrieval_method == "structured_faculty_directory"
    assert "Dr. Radhika M Pai" in response.text


def test_chat_contract_keeps_department_alias_faculty_result(chat_router, monkeypatch):
    router = chat_router
    monkeypatch.setattr(
        router,
        "hybrid_search",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("general RAG should be skipped")),
    )
    monkeypatch.setattr(
        router,
        "generate_answer",
        lambda request: (_ for _ in ()).throw(AssertionError("LLM should be skipped")),
    )

    response = router.chat_query(ChatRequest(
        message="list professors in CSE department",
        session_id="faculty-edge-2",
    ))

    assert response.confidence == "high"
    assert len(response.citations) == 1
    assert "School of Computer Engineering has 180 faculty records" in response.text
    assert "180." in response.text
