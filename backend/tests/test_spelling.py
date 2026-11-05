from app.rag.spelling import correct_query, correct_word


def test_common_typos_are_corrected_against_the_corpus():
    assert correct_query("minimun attendence requred") == "minimum attendance required"
    assert correct_query("cutof rank for computer sciense and enginering") == "cutoff rank for computer science and engineering"
    assert correct_query("when is chirstmas on the acadmic calender?") == "when is christmas on the academic calendar?"  # swapped letters = 1 edit
    assert correct_query("where is dr radhka m pai cabn?") == "where is dr radhika m pai cabin?"


def test_correct_words_numbers_codes_and_short_words_are_left_alone():
    for q in ["What is the minimum attendance required?", "list cse professors", "when is revels",
              "what are the midsem dates", "CES 2203 credits in 2026", "is there a library in AB5"]:
        assert correct_query(q) == q


def test_other_forms_of_known_words_are_left_alone():
    assert correct_word("hostels") is None  # "hostel" is in the documents
    assert correct_word("timings") is None


def test_case_and_punctuation_are_kept():
    assert correct_query("Placment eligiblity?") == "Placement eligibility?"
