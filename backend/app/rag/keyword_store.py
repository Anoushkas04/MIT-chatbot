from functools import lru_cache

import numpy as np
from rank_bm25 import BM25Okapi

from app.rag.store import get_store
from app.rag.text_norm import index_tokens as _tokens


class KeywordStore:
    def __init__(self, records: list[dict]):
        self.records = records
        self.index = BM25Okapi([
            _tokens(
                f"{record.get('source_file') or record.get('source', '')} "
                f"{record.get('retrieval_text', '')} {record.get('text', '')}"
            )
            for record in records
        ])

    def search(self, query: str, k: int = 12) -> list[dict]:
        tokens = _tokens(query)
        if not tokens or not self.records:
            return []
        scores = self.index.get_scores(tokens)
        indices = np.argsort(-scores)[:k]
        maximum = float(scores[indices[0]]) if len(indices) else 0.0
        if maximum <= 0:
            return []
        return [
            {**self.records[int(index)], "score": float(scores[index] / maximum), "retrieval_method": "bm25"}
            for index in indices if scores[index] > 0
        ]


@lru_cache
def get_keyword_store() -> KeywordStore:
    return KeywordStore(get_store().chunks)


def clear_keyword_cache() -> None:
    get_keyword_store.cache_clear()
