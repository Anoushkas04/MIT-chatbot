import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as database
import app.llm as llm
from app.rag.ingest import api_embedding_texts

TEXTS = [f"passage {i} " + "word " * 300 for i in range(60)]  # ~460 estimated tokens each


@pytest.fixture
def gemini(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'cache.db'}")
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine))
    monkeypatch.setattr(llm, "GEMINI_EMBEDDINGS_ENABLED", True)
    monkeypatch.setattr(llm, "GEMINI_API_KEY", "test-key-123456")
    monkeypatch.setattr(llm, "get_client", lambda: object())
    clock = {"now": 0.0, "slept": 0.0, "requests": []}
    monkeypatch.setattr(llm.time, "monotonic", lambda: clock["now"])

    def sleep(seconds):
        clock["now"] += seconds
        clock["slept"] += seconds

    monkeypatch.setattr(llm.time, "sleep", sleep)

    def fake_batch(client, batch):
        clock["requests"].append((clock["now"], sum(llm.estimate_tokens(t) for t in batch)))
        clock["now"] += 1  # each request takes a second
        return [[1.0, float(len(t))] for t in batch]

    monkeypatch.setattr(llm, "_embed_batch_with_retry", fake_batch)
    return clock


def test_requests_stay_under_the_per_request_and_per_minute_token_limits(gemini):
    vectors, label = llm.embed_texts_labelled(TEXTS)
    assert label.startswith("gemini:") and len(vectors) == len(TEXTS)
    assert all(tokens <= llm.EMBED_REQUEST_TOKENS for _, tokens in gemini["requests"])
    for start, _ in gemini["requests"]:
        window = sum(t for when, t in gemini["requests"] if start <= when < start + 60)
        assert window <= llm.EMBED_TOKENS_PER_MINUTE
    assert gemini["slept"] > 0  # it waited instead of hitting the limit


def test_a_build_stops_at_its_time_limit_and_the_next_one_continues(gemini, monkeypatch):
    monkeypatch.setattr(llm, "EMBED_BUILD_SECONDS", 30)  # shorter than the wait for the next minute's budget
    _, label = llm.embed_texts_labelled(TEXTS)
    assert label == llm.LOCAL_EMBEDDER  # not finished: still local, never a mixed index
    first = dict(llm.last_embedding_progress)
    assert 0 < first["embedded"] < first["needed"] == len(TEXTS)
    monkeypatch.setattr(llm, "EMBED_BUILD_SECONDS", 10_000)
    _, label = llm.embed_texts_labelled(TEXTS)
    assert label.startswith("gemini:") and llm.last_embedding_progress["embedded"] == len(TEXTS)


def test_skipped_records_get_an_empty_vector_and_cost_nothing(gemini):
    vectors, label = llm.embed_texts_labelled(["a b c", "d e f"], api_texts=["short a b c", ""])
    assert label.startswith("gemini:") and vectors[1] == [0.0] * 768
    assert sum(t for _, t in gemini["requests"]) == llm.estimate_tokens("short a b c")


def test_gemini_text_drops_the_label_and_the_repeated_overlap():
    records = [
        {"source_file": "notice.pdf", "retrieval_text": "Document title: notice.pdf. Document type: notice.", "text": "First part of the notice. " * 3 + "SHARED ENDING TEXT 12345"},
        {"source_file": "notice.pdf", "retrieval_text": "Document title: notice.pdf. Document type: notice.", "text": "SHARED ENDING TEXT 12345 then the second part."},
        {"source_file": "merged_faculty.csv", "text": "Dr. X, Professor"},
    ]
    api = api_embedding_texts(records)
    assert api[1] == "notice\nthen the second part."
    assert api[2] == ""  # answered from the file; not worth embedding tokens
