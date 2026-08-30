import json
import re
from functools import lru_cache

import numpy as np

from app.config import DATA_DIR


def cosine_search(embeddings: np.ndarray, query: np.ndarray, k: int):
    """Return (indices, scores) of the k rows in `embeddings` most similar to `query`."""
    query = np.asarray(query, dtype=np.float32)
    q_norm = np.linalg.norm(query) or 1.0
    e_norms = np.linalg.norm(embeddings, axis=1)
    e_norms[e_norms == 0] = 1.0
    scores = (embeddings @ query) / (e_norms * q_norm)
    top_idx = np.argsort(-scores)[:k]
    return top_idx, scores[top_idx]


class VectorStore:
    def __init__(self):
        chunks_path = DATA_DIR / "chunks.json"
        embeddings_path = DATA_DIR / "embeddings.npy"
        if not chunks_path.exists() or not embeddings_path.exists():
            raise FileNotFoundError("No ingested data found. Run `python -m app.rag.ingest` first.")
        self.chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
        self.embeddings = np.load(embeddings_path)

    def search(self, query_embedding, raw_query: str = "", k: int = 5) -> list[dict]:
        fetch_k = min(k * 15, len(self.chunks))
        idx, scores = cosine_search(self.embeddings, query_embedding, fetch_k)
        candidates = [{**self.chunks[i], "score": float(s)} for i, s in zip(idx, scores)]

        if raw_query:
            words = [w.lower() for w in re.findall(r'\b\w+\b', raw_query) if len(w) >= 3]
            academic_query = any(w in words for w in ["branch", "branches", "program", "programs", "specialization", "specializations", "btech", "course", "courses", "curriculum", "syllabus"])

            for cand in candidates:
                text_lower = cand["text"].lower()
                matched_count = sum(1 for w in words if re.search(r'\b' + re.escape(w) + r'\b', text_lower))
                cand["score"] += matched_count * 0.05

                if academic_query:
                    if "cutoff rank" in text_lower or "course name" in text_lower or "b.tech" in text_lower:
                        cand["score"] += 0.20
                    if any(b in text_lower for b in ["aeronautical", "computer science", "mechatronics", "biotechnology", "civil", "mechanical", "electrical"]):
                        cand["score"] += 0.15

            candidates.sort(key=lambda x: x["score"], reverse=True)

        return candidates[:k]


@lru_cache
def get_store() -> VectorStore:
    return VectorStore()
