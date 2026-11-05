import json
from pathlib import Path

import pytest
from fastapi import HTTPException

import app.moderation_engine as moderation
from app.sentiment import classify

FIXTURES = Path(__file__).parent / "fixtures"


def test_sentiment_on_held_out_messages_beats_the_old_phrase_list():
    rows = [json.loads(l) for l in (FIXTURES / "eval_sentiment_holdout.jsonl").read_text().splitlines() if l.strip()]
    correct = sum(classify(r["text"]) == r["label"] for r in rows)
    assert correct / len(rows) >= 0.8  # 17/20 when written; the old phrase list got 12/20


def test_tone_cues_and_negation():
    assert classify("I need the hall ticket asap, exam is tomorrow") == "Urgent"
    assert classify("I'm so fed up, nobody replies to my emails") == "Frustrated"
    assert classify("great, this cleared up my doubt") == "Positive"  # "doubt" here isn't confusion
    assert classify("the attendance rule isn't fair at all") == "Negative"
    assert classify("when is the end sem exam for cse") == "Neutral"


def _moderate(title, body):
    from app.routers.community_v2 import _moderate

    class User:
        id, name = "u1", "Student"

    return _moderate(None, User(), title, body)


def test_model_review_holds_posts_the_phrase_list_misses_without_a_strike(monkeypatch):
    monkeypatch.setattr("app.providers.complete_text", lambda *a: '{"violation": true, "category": "Harassment & Targeted Abuse"}')
    strikes = []
    monkeypatch.setattr(moderation, "process_user_strike_and_suspension", lambda *a: strikes.append(a))
    with pytest.raises(HTTPException) as err:
        _moderate("Roommate", "उसे सबके सामने बेइज़्ज़त करो")  # not in the English phrase list
    assert err.value.status_code == 400 and "Harassment" in err.value.detail
    assert strikes == []  # a model's call alone never gives a strike


@pytest.mark.parametrize("reply", [None, "not json", '{"violation": false, "category": "None"}', '{"violation": true, "category": "Made up"}'])
def test_unclear_or_missing_model_verdicts_let_the_post_through(monkeypatch, reply):
    monkeypatch.setattr("app.providers.complete_text", lambda *a: reply)
    _moderate("Hostel wifi", "The wifi in block 17 keeps dropping, who do I complain to?")
