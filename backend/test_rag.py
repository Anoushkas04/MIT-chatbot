import numpy as np

from app.rag.chunker import chunk_text
from app.rag.store import cosine_search, get_store_status
from app.llm import synthesize_local_concise_answer
from app.routers.faculty_router import get_faculty


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


def test_chunk_text_rejects_invalid_overlap():
    try:
        chunk_text("useful source text " * 10, size=100, overlap=100)
        raise AssertionError("Expected invalid chunk settings to fail")
    except ValueError:
        pass


def test_chunk_text_keeps_sentence_chunks_within_limit():
    text = ("a" * 600 + ". ") * 3
    chunks = chunk_text(text, size=1000, overlap=200)
    assert len(chunks) >= 2
    assert all(len(chunk) <= 1000 for chunk in chunks)


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


def test_store_status_matches_generated_index():
    status = get_store_status()
    assert status["ready"] is True
    assert status["chunk_count"] == status["embedding_count"]
    assert status["chunk_count"] > 0


def test_local_answer_only_uses_retrieved_evidence():
    context = "[Source (OFFICIAL): directory.csv]\nDr. Example is located in AB5 room 101."
    answer = synthesize_local_concise_answer("Where is Dr. Example?", context)
    assert "AB5 room 101" in answer
    assert "tuition" not in answer.lower()


def test_faculty_directory_uses_csv_source():
    result = get_faculty(query="Radhika Pai", page=1, page_size=5)
    assert result["count"] >= 1
    faculty = result["data"][0]
    assert faculty["cabin"]
    assert faculty["source"] == "manipal_sce_faculty_cabins.csv"


if __name__ == "__main__":
    test_chunk_text()
    test_chunk_text_empty()
    test_chunk_text_rejects_invalid_overlap()
    test_chunk_text_keeps_sentence_chunks_within_limit()
    test_cosine_search_ranks_exact_match_first()
    test_store_status_matches_generated_index()
    test_local_answer_only_uses_retrieved_evidence()
    test_faculty_directory_uses_csv_source()
    print("All checks passed.")
