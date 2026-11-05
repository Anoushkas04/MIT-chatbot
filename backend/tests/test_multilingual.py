import app.multilingual as ml


def test_script_detection_and_answer_language():
    assert ml.detect_script("रेवल्स कब है?") == "hi"
    assert ml.detect_script("ರೆವೆಲ್ಸ್ ಯಾವಾಗ?") == "kn"
    assert ml.detect_script("when is revels") is None
    assert ml.answer_language("en", "ರೆವೆಲ್ಸ್ ಯಾವಾಗ?") == "kn"  # typed in Kannada with English selected
    assert ml.answer_language("hi", "when is revels") == "hi"  # the chosen language wins
    assert ml.answer_language("fr", "when is revels") == "en"


def test_english_questions_are_not_translated(monkeypatch):
    monkeypatch.setattr(ml, "complete_text", lambda *a: (_ for _ in ()).throw(AssertionError("no call")))
    assert ml.search_query("when is revels", "en") == "when is revels"


def test_other_languages_are_searched_in_english(monkeypatch):
    monkeypatch.setattr(ml, "complete_text", lambda system, text: '"When is REVELS?"\n')
    assert ml.search_query("रेवल्स कब है?", "hi") == "When is REVELS?"


def test_translation_failure_or_rambling_falls_back_to_the_question(monkeypatch):
    monkeypatch.setattr(ml, "complete_text", lambda *a: None)
    assert ml.search_query("रेवल्स कब है?", "hi") == "रेवल्स कब है?"
    monkeypatch.setattr(ml, "complete_text", lambda *a: "x" * 500)
    assert ml.search_query("कब?", "hi") == "कब?"


def test_fixed_replies_exist_for_every_language():
    assert set(ml.NO_INFO) == set(ml.LOW_CONFIDENCE) == ml.SUPPORTED


HISTORY = [{"role": "user", "text": "what is the fee for B.Tech CSE"}, {"role": "model", "text": "The fee is ... [E1]"}]


def test_follow_ups_are_detected_and_standalone_questions_are_not():
    assert ml.is_follow_up("and its hostel fees?", HISTORY)
    assert ml.is_follow_up("what about the even semester?", HISTORY)
    assert ml.is_follow_up("for AIML?", HISTORY)  # short: the model decides
    assert not ml.is_follow_up("when are the end semester exams for B.Tech in November", HISTORY)
    assert not ml.is_follow_up("and its hostel fees?", [])  # nothing to follow


def test_follow_ups_are_rewritten_with_the_conversation(monkeypatch):
    seen = {}

    def fake(system, prompt):
        seen["prompt"] = prompt
        return "What are the hostel fees for B.Tech CSE at MIT Manipal?"

    monkeypatch.setattr(ml, "complete_text", fake)
    assert ml.search_query("and its hostel fees?", "en", HISTORY) == "What are the hostel fees for B.Tech CSE at MIT Manipal?"
    assert "fee for B.Tech CSE" in seen["prompt"] and "and its hostel fees?" in seen["prompt"]


def test_standalone_english_questions_make_no_model_call(monkeypatch):
    monkeypatch.setattr(ml, "complete_text", lambda *a: (_ for _ in ()).throw(AssertionError("no call")))
    q = "when are the end semester exams for B.Tech in November"
    assert ml.search_query(q, "en", HISTORY) == q


def test_without_a_model_a_follow_up_borrows_the_previous_question(monkeypatch):
    monkeypatch.setattr(ml, "complete_text", lambda *a: None)
    assert ml.search_query("and its hostel fees?", "en", HISTORY) == "what is the fee for B.Tech CSE and its hostel fees?"
    assert ml.search_query("revels dates", "en", HISTORY) == "revels dates"  # short but standalone
