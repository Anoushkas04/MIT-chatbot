"""Saved API embeddings for index builds (see models.EmbeddingCache).

The Gemini free tier allows 1,000 embedding requests a day and every deploy rebuilds
the index, so without this each deploy would re-embed every chunk. Vectors are looked
up by sha256(model + text) and saved as soon as each batch comes back. Any database
problem just means no cache: the build still works, it only costs more requests.
"""
import hashlib

import numpy as np


def key_for(model: str, text: str) -> str:
    return hashlib.sha256(f"{model}\n{text}".encode("utf-8")).hexdigest()


def _table():
    from app import models
    from app.database import engine

    models.EmbeddingCache.__table__.create(bind=engine, checkfirst=True)  # builds run before app startup
    return models.EmbeddingCache


def load(model: str, texts: list[str]) -> dict[str, list[float]]:
    """Cached vectors for the texts that have one, keyed by cache key."""
    try:
        from app.database import SessionLocal

        table = _table()
        keys = list({key_for(model, t) for t in texts})
        found: dict[str, list[float]] = {}
        db = SessionLocal()
        try:
            for start in range(0, len(keys), 500):
                rows = db.query(table.key, table.vector).filter(table.key.in_(keys[start:start + 500])).all()
                found.update({k: np.frombuffer(v, dtype=np.float32).tolist() for k, v in rows})
        finally:
            db.close()
        return found
    except Exception as exc:
        print(f"Embedding cache unavailable ({exc}); embedding everything.")
        return {}


def save(model: str, texts: list[str], vectors: list[list[float]]) -> None:
    try:
        from app.database import SessionLocal

        table = _table()
        db = SessionLocal()
        try:
            seen = set()
            for text, vector in zip(texts, vectors):
                key = key_for(model, text)
                if key in seen:
                    continue
                seen.add(key)
                db.merge(table(key=key, model=model, vector=np.asarray(vector, dtype=np.float32).tobytes()))
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        print(f"Couldn't save embeddings to the cache ({exc}).")
