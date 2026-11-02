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


def test_local_provider_returns_evidence_markers():
    result = LocalProvider().generate(GenerationRequest(
        question="What attendance is required?",
        system_prompt="",
        evidence=[{"text": "Students require 75 percent attendance."}],
    ))
    assert "75 percent" in result.text
    assert "[E1]" in result.text


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
