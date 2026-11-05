from app.rag.text_norm import expand_query, index_tokens
from app.routers.chat_router import _citation
from app.structured_lookup import calendar_evidence, club_evidence


def test_question_words_and_plurals_are_normalised():
    assert index_tokens("What are the holidays?") == ["holiday"]
    assert index_tokens("exams courses") == ["exam", "course"]


def test_student_phrasing_expands_to_document_words():
    assert "revels" in expand_query("when is the cultural fest")
    assert "end semester" in expand_query("when do end sem exams start")


def test_calendar_answers_month_and_phrase_questions():
    holidays = calendar_evidence("when are the holidays in november")[0]["text"]
    assert "Deepavali" in holidays and "2026-11-21" in holidays
    assert holidays.count("Deepavali") == 1  # "Deepavali" and "Deepavali (holiday)" are one entry
    fest = calendar_evidence("what dates is the cultural fest this year")[0]["text"]
    assert "REVELS" in fest
    exams = calendar_evidence("when do end sem exams start")[0]["text"]
    assert "End Semester Exams start" in exams and "Makeup" not in exams


def test_calendar_stays_out_of_non_date_questions():
    assert calendar_evidence("how is cgpa calculated") == []


def test_clubs_match_topics_and_link_their_own_page():
    robotics = club_evidence("which clubs are there for robotics")
    assert robotics and all(r["kind"] == "club" for r in robotics)
    assert any("Mechatronics" in r["source"] for r in robotics)
    full = club_evidence("list technical clubs")
    assert len(full) == 1 and "Technical" in full[0]["text"]
    kalakriya = [r for r in club_evidence("tell me about kalakriya club") if "Kalakriya" in r["source"]]
    assert kalakriya and kalakriya[0]["url"] is None  # the source links it to another club's page


def test_citations_say_where_to_go():
    club = club_evidence("tell me about the astronomy club")[0]
    citation = _citation(1, club, "clubs.pdf", None)
    assert citation.kind == "club" and citation.source_url.startswith("https://")
    doc = _citation(2, {"text": "x", "page_number": 4}, "Regulations 2026 B.Tech.pdf", None)
    assert doc.kind == "document" and doc.title == "Regulations 2026 B.Tech" and doc.page_number == 4
    faculty = _citation(1, {"text": "x"}, "merged_faculty.csv", {"kind": "person", "records": [{"name": "Dr. A B", "dept": "X"}]})
    assert faculty.source_url == "/utilities?section=professors&q=Dr.%20A%20B"


def test_faculty_lists_understand_common_school_names():
    from app.faculty_directory import lookup_faculty

    expected = {
        "Can you give me the list of all the professors in school of computing": "School of Computer Engineering",
        "list all maths faculty": "School of Basic Sciences, Humanities & Management",
        "show biotech professors": "School of Civil & Chemical Engineering",
    }
    for question, school in expected.items():
        result = lookup_faculty(question)
        assert result and result["kind"] == "department_list", question
        assert {r["dept"] for r in result["records"]} == {school}
