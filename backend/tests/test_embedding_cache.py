import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as database
import app.llm as llm

TEXTS = [f"chunk number {i}" for i in range(250)]


@pytest.fixture
def gemini(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'cache.db'}")
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine))
    monkeypatch.setattr(llm, "GEMINI_EMBEDDINGS_ENABLED", True)
    monkeypatch.setattr(llm, "GEMINI_API_KEY", "test-key-123456")
    monkeypatch.setattr(llm, "get_client", lambda: object())
    calls = {"requests": 0, "fail_after": None}

    def fake_batch(client, batch):
        if calls["fail_after"] is not None and calls["requests"] >= calls["fail_after"]:
            raise RuntimeError("429 RESOURCE_EXHAUSTED PerDay")
        calls["requests"] += 1
        return [[float(len(t)), 1.0] for t in batch]

    monkeypatch.setattr(llm, "_embed_batch_with_retry", fake_batch)
    return calls


def test_rebuilds_reuse_cached_embeddings(gemini):
    vectors, label = llm.embed_texts_labelled(TEXTS)
    assert label.startswith("gemini:") and len(vectors) == 250
    assert gemini["requests"] == 3  # batches of 100
    gemini["requests"] = 0
    again, label = llm.embed_texts_labelled(TEXTS)
    assert label.startswith("gemini:") and again == vectors and gemini["requests"] == 0


def test_a_build_stopped_by_the_quota_continues_next_time(gemini):
    gemini["fail_after"] = 1
    vectors, label = llm.embed_texts_labelled(TEXTS)
    assert label == llm.LOCAL_EMBEDDER  # never a mixed index
    gemini["fail_after"], gemini["requests"] = None, 0
    vectors, label = llm.embed_texts_labelled(TEXTS)
    assert label.startswith("gemini:")
    assert gemini["requests"] == 2  # the first 100 were saved before the failure
