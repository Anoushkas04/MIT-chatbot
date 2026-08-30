import numpy as np

from app.rag.chunker import chunk_text
from app.rag.store import cosine_search


def test_chunk_text():
    text = "x" * 2500
    chunks = chunk_text(text, size=1000, overlap=150)
    assert len(chunks) == 3
    assert chunks[0] == text[0:1000]
    assert chunks[1] == text[850:1850]
    assert all(len(c) <= 1000 for c in chunks)


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_cosine_search_ranks_exact_match_first():
    embeddings = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.9, 0.1, 0.0],
        ],
        dtype=np.float32,
    )
    query = np.array([1.0, 0.0, 0.0], dtype=np.float32)

    idx, scores = cosine_search(embeddings, query, k=2)

    assert idx[0] == 0
    assert scores[0] > scores[1]


if __name__ == "__main__":
    test_chunk_text()
    test_chunk_text_empty()
    test_cosine_search_ranks_exact_match_first()
    print("All checks passed.")
