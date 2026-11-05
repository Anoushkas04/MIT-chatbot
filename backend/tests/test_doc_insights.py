from app.rag.doc_insights import build_insights

FOOTER = "We use cookies on this website to make your browsing experience better."


def _records():
    placement = [
        {"source_file": "placement.pdf", "document_type": "guidelines", "text": f"Students must register on the placement portal before the placement drive. The placement portal closes once the placement drive begins. {FOOTER}"},
        {"source_file": "placement.pdf", "document_type": "guidelines", "text": "A student under academic probation is not allowed to register on the placement portal for any placement drive."},
    ]
    syllabus = [
        {"source_file": "syllabus.pdf", "document_type": "syllabus", "text": f"Operating Systems covers process scheduling and memory management in detail for every student. Operating Systems lab uses process scheduling simulators. {FOOTER}"},
        {"source_file": "syllabus.pdf", "document_type": "syllabus", "text": "Memory management, paging and process scheduling are assessed in the operating systems examination."},
    ]
    return placement + syllabus


def test_keywords_are_phrases_distinctive_to_each_document():
    insights = build_insights(_records())
    assert any("placement portal" in k.lower() or "placement drive" in k.lower() for k in insights["placement.pdf"]["keywords"])
    assert any("process scheduling" in k.lower() or "operating systems" in k.lower() for k in insights["syllabus.pdf"]["keywords"])
    assert not any("cookie" in k.lower() or "browsing" in k.lower() for d in insights.values() for k in d["keywords"])


def test_summaries_are_whole_prose_sentences_without_boilerplate():
    insights = build_insights(_records())
    summary = insights["placement.pdf"]["summary"]
    assert summary and summary.endswith(".") and "cookies" not in summary  # repeated footer skipped
    assert insights["syllabus.pdf"]["summary"] == ""  # table-like document types show keywords only
