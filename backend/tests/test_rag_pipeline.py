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


def test_local_provider_returns_evidence_markers():
    result = LocalProvider().generate(GenerationRequest(
        question="What attendance is required?",
        system_prompt="",
        evidence=[{"text": "Students require 75 percent attendance."}],
    ))
    assert "75 percent" in result.text
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
