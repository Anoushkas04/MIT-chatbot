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
