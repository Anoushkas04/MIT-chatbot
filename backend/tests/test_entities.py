from app.faculty_directory import lookup_faculty
from app.rag.entities import extract
from app.structured_lookup import calendar_evidence


def test_course_codes_semesters_years_months_and_departments():
    e = extract("CES 2203 credits in the fourth semester of BTech CSE 2026-27, and IV sem labs in November")
    assert e.course_codes == ["CES 2203"]  # "CSE 2026" is a department and a year, not a code
    assert e.semesters == [4]
    assert e.academic_year == "2026-2027" and 2026 in e.years
    assert e.months == [11]
    assert e.department_code == "CSE"
    assert {"curriculum", "date"} <= e.intents
    assert extract("what about the even semester exams").semester_parity == "even"
    assert extract("Where is Dr. Radhika M Pai's cabin?").intents == {"person"}


def test_a_named_professor_wins_over_the_department_list():
    result = lookup_faculty("Where can I find Professor Sanjay Singh in the SCE faculty rooms?")
    assert result["kind"] == "person" and result["records"][0]["name"].endswith("Sanjay Singh")
    assert lookup_faculty("list all professors in the SCE")["kind"] == "department_list"


def test_curriculum_and_policy_questions_dont_trigger_other_lookups():
    assert "curriculum" in extract("From the CSE syllabus, list subjects in the fourth semester of BTech CSE 2026.").intents
    assert calendar_evidence("What attendance is required to write the end-semester examination?") == []
    christmas = calendar_evidence("What date is Christmas marked on the 2026-27 academic calendar?")
    assert christmas and "2026-12-25" in christmas[0]["text"] and christmas[0]["text"].count("\n- ") == 1
