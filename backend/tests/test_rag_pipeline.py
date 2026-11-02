import json

import pymupdf as fitz

from app.answer_verifier import NO_EVIDENCE_MESSAGE, verify_answer
from app.providers.base import GenerationRequest
from app.providers.local_provider import LocalProvider
from app.rag.page_loader import load_corpus


def test_page_loader_preserves_pdf_page_metadata(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    path = docs / "policy.pdf"
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text(
            (72, 72),
            "Minimum attendance is 75 percent. Students below this threshold cannot write the end semester examination.",
        )
        document.save(path)

    pages, chunks = load_corpus(docs, tmp_path / "images", render_images=False)
    assert len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert pages[0]["source"] == "policy.pdf"
    assert chunks[0]["document_id"] == pages[0]["document_id"]
    assert chunks[0]["page_id"] == pages[0]["page_id"]


def test_scanned_scope_renders_only_pages_without_text(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    path = docs / "mixed.pdf"
    with fitz.open() as document:
        text_page = document.new_page()
        text_page.insert_text(
            (72, 72),
            "This text page is intentionally long enough to become a normal searchable text chunk in the index.",
        )
        document.new_page()
        document.save(path)

    pages, _ = load_corpus(
        docs,
        tmp_path / "images",
        render_images=True,
        render_dpi=72,
        visual_scope="scanned",
    )
    assert pages[0]["image_path"] is None
    assert pages[0]["is_scanned"] is False
    assert pages[1]["image_path"].endswith("p0002.png")
    assert pages[1]["is_scanned"] is True


def test_visual_metadata_tokens_handle_years_and_cs_alias():
    from app.rag.visual_store import _metadata_tokens

    query = _metadata_tokens("first year computer science BTech subjects 2026")
    source = _metadata_tokens("First year CS 2026 B.Tech.pdf")
    assert {"first", "year", "cs", "26"}.issubset(query.intersection(source))


def test_metadata_tokens_split_camel_case_and_expand_course_aliases():
    from app.rag.visual_store import _metadata_tokens

    attachment = _metadata_tokens("AttachmentMIT_INR_compressed.pdf")
    machine_learning = _metadata_tokens("machine learning course plan")
    database_systems = _metadata_tokens("database systems course plan")
    operating_systems = _metadata_tokens("operating systems course plan")

    assert {"attachment", "mit", "inr"}.issubset(attachment)
    assert "ml" in machine_learning
    assert "dbs" in database_systems
    assert "os" in operating_systems


def test_query_expansion_adds_course_filename_aliases():
    from app.rag.hybrid import _expanded_query, _source_title_match_score

    assert _expanded_query("machine learning course plan").endswith("ml")
    assert _expanded_query("mechanical engineering cutoff").endswith("me")
    assert _expanded_query("database systems course plan").endswith("dbs")
    assert _expanded_query("operating systems course plan").endswith("os")
    query = "What topics are in the machine learning course plan?"
    assert _source_title_match_score(query, "CP_ML.pdf") > _source_title_match_score(
        query, "BRE - Course Plan.pdf"
    )
    assert _source_title_match_score(
        "What happens when a student has low attendance?",
        "Impartus Lecture Capture - Student Guide.pdf",
    ) < 3


def test_document_metadata_recognizes_department_and_short_academic_year():
    from app.rag.metadata import infer_document_metadata

    mechatronics = infer_document_metadata("BTech_MechX_Syllabus_2026.pdf")
    calendar = infer_document_metadata("Academic Calendar 26-27.pdf")
    first_year = infer_document_metadata("First year CS 2026 B.Tech.pdf")
    aeronautical = infer_document_metadata(
        "BTech_Aero_Syllabus_2022_FY.pdf",
        "This common first-year table mentions Computer Science and Engineering.",
    )

    assert mechatronics["department_code"] == "MECHX"
    assert mechatronics["document_type"] == "syllabus"
    assert calendar["academic_year"] == "2026-2027"
    assert calendar["document_type"] == "academic_calendar"
    assert first_year["department_code"] == "CSE"
    assert first_year["document_type"] == "curriculum"
    assert aeronautical["department_code"] == "AERO"


def test_calendar_ocr_is_split_into_month_search_segments():
    from app.rag.local_ocr import _calendar_events, _calendar_segments

    def line(text, left, top, right, bottom, confidence=0.9):
        return {
            "text": text,
            "confidence": confidence,
            "box": [[left, top], [right, top], [right, bottom], [left, bottom]],
        }

    lines = [
        line("July -26", 50, 50, 150, 80),
        line("Aug -26", 250, 50, 350, 80),
        line("6 M Makeup Exams Results", 50, 100, 180, 120),
        line("7 T", 50, 130, 80, 150),
        line("15 S Independence Day", 250, 100, 380, 120),
    ]
    page = {"source": "Academic Calendar 26-27.pdf", "page_number": 1, "document_id": "calendar"}
    segments = _calendar_segments(lines, (500, 500), page)
    events = _calendar_events(segments, page)

    assert [segment["title"] for segment in segments] == ["July 2026", "August 2026"]
    assert "Makeup Exams Results" in segments[0]["text"]
    assert any(event["date"] == "2026-07-06" and "Makeup Exams" in event["title"] for event in events)
    assert any(event["date"] == "2026-08-15" and "Independence Day" in event["title"] for event in events)


def test_ingestion_turns_local_ocr_segments_into_text_chunks(tmp_path, monkeypatch):
    import app.rag.ingest as ingest

    image_dir = tmp_path / "page_images"
    image_dir.mkdir()
    (image_dir / "page.png").write_bytes(b"not-read-because-ocr-is-mocked")
    pages = [{
        "id": "doc-p0001",
        "page_id": "doc-p0001",
        "document_id": "doc",
        "source": "Academic Calendar 26-27.pdf",
        "page_number": 1,
        "image_path": "page_images/page.png",
        "is_scanned": True,
        "department_code": None,
        "department": None,
        "programme": None,
        "academic_year": "2026-2027",
        "semester": None,
        "document_type": "academic_calendar",
    }]
    monkeypatch.setattr(ingest, "LOCAL_OCR_ENABLED", True)
    monkeypatch.setattr(ingest, "extract_page", lambda *args, **kwargs: {
        "text": "Academic calendar July 2026. Makeup examination results are published on 6 July 2026.",
        "engine": "rapidocr_onnxruntime",
        "average_confidence": 0.91,
        "line_count": 3,
        "segments": [{
            "title": "July 2026",
            "text": "Academic calendar July 2026. Makeup examination results are published on 6 July 2026.",
            "metadata": {"calendar_year": 2026, "calendar_month": 7},
        }],
        "calendar_events": [{"date": "2026-07-06", "title": "Makeup examination results"}],
    })

    records, events = ingest._ocr_scanned_pages(pages, image_dir, lambda *args: None)

    assert records[0]["record_type"] == "ocr_chunk"
    assert records[0]["calendar_month"] == 7
    assert records[0]["academic_year"] == "2026-2027"
    assert events[0]["date"] == "2026-07-06"
    assert pages[0]["extraction_method"] == "rapidocr_onnxruntime"


def test_evidence_merge_preserves_both_source_partitions():
    from app.routers.chat_router import merge_evidence

    official = [{"source": f"official-{index}"} for index in range(4)]
    community = [{"source": f"community-{index}"} for index in range(3)]

    official_first = merge_evidence(official, community, prefer_community=False)
    community_first = merge_evidence(official, community, prefer_community=True)

    assert [item["source"] for item in official_first] == [
        "official-0", "official-1", "official-2", "community-0",
    ]
    assert [item["source"] for item in community_first] == [
        "community-0", "community-1", "official-0", "official-1",
    ]


def test_hybrid_promotes_stronger_scanned_source_metadata(monkeypatch):
    from types import SimpleNamespace
    import app.rag.hybrid as hybrid

    text_hit = {"id": "text-1", "source": "general-handbook.pdf", "text": "academic calendar", "score": 1.0}
    visual_hit = {
        "id": "visual-1", "page_id": "visual-1", "source": "Academic Calendar 26-27.pdf",
        "page_number": 1, "text": "", "image_path": "page_images/calendar.png", "score": 20.0,
        "metadata_matches": 4,
    }
    monkeypatch.setattr(hybrid, "embed_query", lambda query: [0.0])
    monkeypatch.setattr(hybrid, "get_store", lambda: SimpleNamespace(search=lambda *args, **kwargs: [text_hit]))
    monkeypatch.setattr(hybrid, "get_keyword_store", lambda: SimpleNamespace(search=lambda *args, **kwargs: [text_hit]))
    monkeypatch.setattr(hybrid, "get_visual_store", lambda: SimpleNamespace(search=lambda *args, **kwargs: [visual_hit]))
    monkeypatch.setattr(hybrid, "VISUAL_RAG_ENABLED", True)

    results = hybrid.hybrid_search("What dates are in Academic Calendar 2026-27?", final_k=2)
    assert results[0]["source"] == "Academic Calendar 26-27.pdf"
    assert results[0]["promoted_visual"] is True
    assert results[0]["score"] == 1.0


def test_hybrid_uses_selected_department_context(monkeypatch):
    from types import SimpleNamespace
    import app.rag.hybrid as hybrid

    mechanical = {
        "id": "mech", "source": "BTech_Mech_Syllabus_2026.pdf", "text": "Programme subjects",
        "score": 0.9, "department_code": "ME",
    }
    computer_science = {
        "id": "cse", "source": "BTech_CSE_Syllabus_2026.pdf", "text": "Programme subjects",
        "score": 0.8, "department_code": "CSE",
    }
    monkeypatch.setattr(hybrid, "embed_query", lambda query: [0.0])
    monkeypatch.setattr(
        hybrid,
        "get_store",
        lambda: SimpleNamespace(search=lambda *args, **kwargs: [mechanical, computer_science]),
    )
    monkeypatch.setattr(
        hybrid,
        "get_keyword_store",
        lambda: SimpleNamespace(search=lambda *args, **kwargs: [mechanical, computer_science]),
    )
    monkeypatch.setattr(hybrid, "VISUAL_RAG_ENABLED", False)

    results = hybrid.hybrid_search("What subjects are in my department?", department="CSE", final_k=2)

    assert results[0]["department_code"] == "CSE"


def test_record_query_priority_prefers_calendar_month_year_and_curriculum_overview():
    from app.rag.hybrid import _key, _record_query_priority

    july_2026 = {"calendar_month": 7, "calendar_year": 2026}
    july_2027 = {"calendar_month": 7, "calendar_year": 2027}
    overview = {"page_number": 1, "document_type": "curriculum"}
    detail = {"page_number": 6, "document_type": "curriculum"}

    assert _record_query_priority(july_2026, "Makeup exam results in July 2026") > _record_query_priority(
        july_2027, "Makeup exam results in July 2026"
    )
    assert _record_query_priority(overview, "What first year subjects are offered?") > _record_query_priority(
        detail, "What first year subjects are offered?"
    )
    assert _key({"id": "page-1-chunk-a", "page_id": "page-1"}) != _key(
        {"id": "page-1-chunk-b", "page_id": "page-1"}
    )


def test_local_provider_returns_evidence_markers():
    result = LocalProvider().generate(GenerationRequest(
        question="What attendance is required?",
        system_prompt="",
        evidence=[{"text": "Students require 75 percent attendance."}],
    ))
    assert "75 percent" in result.text
    assert "[E1]" in result.text
    assert not result.text.startswith("Based on the retrieved")


def test_local_provider_selects_a_concise_relevant_sentence():
    result = LocalProvider().generate(GenerationRequest(
        question="What is the minimum attendance requirement?",
        system_prompt="",
        evidence=[{
            "text": (
                "This section describes the grading system and contains general introductory material. "
                "Only students with a minimum attendance of 75% may appear for the end semester examination. "
                "A separate rule explains grade-point calculations for completed courses."
            ),
        }],
    ))
    assert "minimum attendance of 75%" in result.text
    assert "general introductory material" not in result.text
    assert len(result.text) < 400


def test_system_prompt_does_not_duplicate_raw_evidence():
    from app.prompts import build_system_prompt

    prompt = build_system_prompt(
        role="student",
        language="en",
        context_chunks=[{"text": "RAW EVIDENCE MUST NOT BE DUPLICATED"}],
    )
    assert "RAW EVIDENCE MUST NOT BE DUPLICATED" not in prompt
    assert "at most 120 words" in prompt
    assert "supplied separately" in prompt


def test_local_provider_is_honest_about_visual_only_evidence():
    result = LocalProvider().generate(GenerationRequest(
        question="What date is shown?",
        system_prompt="",
        evidence=[{"text": "", "image_path": "page_images/calendar.png"}],
    ))
    assert "cannot interpret" in result.text
    assert "[E1]" in result.text


def test_verifier_rejects_empty_evidence():
    answer, warnings = verify_answer("A confident but unsupported claim.", [])
    assert answer == NO_EVIDENCE_MESSAGE
    assert warnings == ["no_evidence"]


def test_verifier_removes_invalid_markers():
    answer, warnings = verify_answer("Valid [E1], invalid [E9].", [{"text": "proof"}])
    assert "[E1]" in answer
    assert "[E9]" not in answer
    assert "invalid_citation_markers_removed" in warnings


def test_retrieval_fixture_has_required_coverage():
    path = __import__("pathlib").Path(__file__).parent / "fixtures" / "rag_queries.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) >= 40
    assert {row["modality"] for row in rows} >= {"text", "visual", "csv"}
    assert all(row.get("question") and row.get("expected_source") for row in rows)


def _generation_request():
    return GenerationRequest(
        question="What is the rule?",
        system_prompt="Ground every claim.",
        evidence=[{"source": "policy.pdf", "page_number": 2, "text": "The rule is 75 percent."}],
    )


def test_openai_adapter_uses_responses_api():
    from types import SimpleNamespace
    from app.providers.openai_provider import OpenAIProvider

    captured = {}
    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: captured.update(kwargs) or SimpleNamespace(output_text="Rule [E1]")))
    result = provider.generate(_generation_request())
    assert result.text == "Rule [E1]"
    assert captured["instructions"] == "Ground every claim."
    assert captured["input"][0]["content"][0]["type"] == "input_text"


def test_anthropic_adapter_uses_messages_api():
    from types import SimpleNamespace
    from app.providers.anthropic_provider import AnthropicProvider

    captured = {}
    block = SimpleNamespace(type="text", text="Rule [E1]")
    provider = AnthropicProvider.__new__(AnthropicProvider)
    provider.client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kwargs: captured.update(kwargs) or SimpleNamespace(content=[block])))
    result = provider.generate(_generation_request())
    assert result.text == "Rule [E1]"
    assert captured["system"] == "Ground every claim."


def test_gemini_adapter_uses_generate_content():
    from types import SimpleNamespace
    from app.providers.gemini_provider import GeminiProvider

    captured = {}
    provider = GeminiProvider.__new__(GeminiProvider)
    provider.client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs: captured.update(kwargs) or SimpleNamespace(text="Rule [E1]")))
    result = provider.generate(_generation_request())
    assert result.text == "Rule [E1]"
    assert captured["contents"][0].endswith("do not guess.")


def test_provider_failure_falls_back_to_grounded_local_answer(monkeypatch):
    import app.providers.registry as registry

    class FailingProvider:
        name = "openai"

        def generate(self, request):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(registry, "get_provider", lambda: FailingProvider())
    result = registry.generate_answer(_generation_request())
    assert result.provider == "local"
    assert "75 percent" in result.text
    assert "[E1]" in result.text


def test_relevance_filter_rejects_unrelated_high_score_result():
    from app.routers.chat_router import filter_chunk_relevance

    result = filter_chunk_relevance(
        [{
            "source": "Official Clubs Directory.pdf",
            "text": "The official electronics club email address is club@example.edu.",
            "score": 1.0,
        }],
        "What is the official MIT Manipal policy for teleportation portals?",
        "simple_factual",
    )
    assert result == []


def test_relevance_filter_keeps_visual_source_metadata_match():
    from app.routers.chat_router import filter_chunk_relevance

    result = filter_chunk_relevance(
        [{
            "source": "Academic Calendar 26-27.pdf",
            "text": "",
            "image_path": "page_images/calendar.png",
            "score": 0.8,
        }],
        "What dates are in the academic calendar for 2026-27?",
        "simple_factual",
    )
    assert result[0]["source"] == "Academic Calendar 26-27.pdf"


def test_generation_key_does_not_silently_change_embedding_space(monkeypatch):
    import app.llm as llm

    monkeypatch.setattr(llm, "GEMINI_API_KEY", "configured-generation-key")
    monkeypatch.setattr(llm, "GEMINI_EMBEDDINGS_ENABLED", False)
    monkeypatch.setattr(
        llm,
        "get_client",
        lambda: (_ for _ in ()).throw(AssertionError("remote embeddings should not be called")),
    )
    vector = llm.embed_query("minimum attendance requirement")
    assert len(vector) == 768
