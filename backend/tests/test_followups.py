from app.followups import _title, split_model_followups, suggest


def test_model_followups_are_split_off_the_answer():
    text, followups = split_model_followups("Minimum attendance is 75% [E1].\n\nFollow-up questions: What is condonation? | When are makeup exams?")
    assert text == "Minimum attendance is 75% [E1]."
    assert followups == ["What is condonation?", "When are makeup exams?"]
    assert split_model_followups("No follow-ups here [E1].") == ("No follow-ups here [E1].", [])


def test_suggestions_must_be_answerable_from_the_same_evidence():
    evidence = [{"retrieval_method": "structured_calendar", "kind": "calendar", "source_file": "Academic Calendar 26-27 (1).pdf",
                 "text": "Official MIT Manipal Academic Calendar 2026-27. Matching entries:\n- 2026-11-14 (Saturday) — End Semester Exams start"}]
    out = suggest("when do end sem exams start", evidence, ["What is the hostel wifi password?"], None)
    assert "What is on the academic calendar in November 2026?" in out
    assert "What is the hostel wifi password?" not in out  # the evidence can't answer it
    assert suggest("anything", [], ["What is X?"], None) == []


def test_document_titles_are_readable():
    assert _title("PLACEMENT GUIDELINES 13 JULY 2024 FINAL_250905_124353.pdf") == "Placement Guidelines"
    assert _title("MIT - UG - Hand Book-- 2024 - Revised.pdf") == "MIT UG Handbook 2024"
