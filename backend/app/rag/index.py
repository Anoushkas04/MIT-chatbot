"""Incremental maintenance of the chatbot's document index (data/chunks.json + embeddings.npy).

Adding or replacing a file re-embeds only that file's chunks; removing one drops them.
Vectors from different embedders (Gemini vs the local hash fallback in llm.embed_texts)
can't be compared, so every write checks the stored embedder and vector size and asks
for a full rebuild instead of mixing them.
"""
import datetime
import json
import threading
from pathlib import Path
from typing import Optional

import numpy as np

from app.config import DATA_DIR, DOCS_DIR, EMBEDDING_MODEL, GEMINI_API_KEY
from app.llm import embed_texts, is_valid_key
from app.rag.loaders import load_documents, load_file
from app.rag.store import get_store

CHUNKS = DATA_DIR / "chunks.json"
EMBEDDINGS = DATA_DIR / "embeddings.npy"
META = DATA_DIR / "index_meta.json"

_lock = threading.Lock()  # one writer at a time: uploads, removals and rebuilds
rebuild_state = {"running": False, "started_at": None, "finished_at": None, "error": None, "chunks": None}


class NeedsFullRebuild(RuntimeError):
    pass


def _file_of(chunk: dict) -> str:
    # Indexes built before chunks carried "file" only have the citation label.
    return chunk.get("file") or chunk["source"]


def current_embedder() -> str:
    return f"gemini:{EMBEDDING_MODEL}" if is_valid_key(GEMINI_API_KEY) else "local-hash"


def exists() -> bool:
    return CHUNKS.exists() and EMBEDDINGS.exists()


def meta() -> dict:
    if not META.exists():
        return {}
    try:
        return json.loads(META.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save(chunks: list, vectors: np.ndarray, embedder: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    counts: dict = {}
    for c in chunks:
        counts[_file_of(c)] = counts.get(_file_of(c), 0) + 1
    # Write to temp files then swap, so a crash never leaves a half-written index.
    tmp_chunks, tmp_vec = CHUNKS.with_suffix(".json.tmp"), DATA_DIR / "embeddings.tmp.npy"
    tmp_chunks.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    np.save(tmp_vec, vectors.astype(np.float32))
    tmp_chunks.replace(CHUNKS)
    tmp_vec.replace(EMBEDDINGS)
    META.write_text(
        json.dumps(
            {
                "embedder": embedder,
                "dim": int(vectors.shape[1]) if vectors.size else None,
                "built_at": datetime.datetime.utcnow().isoformat() + "Z",
                "total_chunks": len(chunks),
                "sources": counts,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    get_store.cache_clear()  # the chatbot picks up the new index on its next question


def _load() -> tuple[list, np.ndarray]:
    return json.loads(CHUNKS.read_text(encoding="utf-8")), np.load(EMBEDDINGS)


def _embed(records: list) -> np.ndarray:
    return np.array(embed_texts([r["text"] for r in records]), dtype=np.float32)


def rebuild() -> int:
    """Re-reads every document in DOCS_DIR and rebuilds the whole index."""
    with _lock:
        records = load_documents(DOCS_DIR)
        vectors = _embed(records) if records else np.zeros((0, 0), dtype=np.float32)
        _save(records, vectors, current_embedder())
        return len(records)


def rebuild_in_background() -> bool:
    """Starts a full rebuild on a thread; False if one is already running."""
    if rebuild_state["running"]:
        return False
    rebuild_state.update(running=True, started_at=datetime.datetime.utcnow().isoformat() + "Z", finished_at=None, error=None, chunks=None)

    def run():
        try:
            rebuild_state["chunks"] = rebuild()
        except Exception as e:  # surfaced on the dataset page
            rebuild_state["error"] = str(e)
        finally:
            rebuild_state.update(running=False, finished_at=datetime.datetime.utcnow().isoformat() + "Z")

    threading.Thread(target=run, daemon=True).start()
    return True


def _check_compatible(new: np.ndarray, old: np.ndarray) -> None:
    m = meta()
    if m.get("embedder") and m["embedder"] != current_embedder():
        raise NeedsFullRebuild(f"The index was built with {m['embedder']} but the server now uses {current_embedder()}. Run a full rebuild.")
    if old.size and new.size and old.shape[1] != new.shape[1]:
        raise NeedsFullRebuild("New vectors don't match the index size (the embedding service may have fallen back). Run a full rebuild.")


def upsert_file(path: Path) -> int:
    """(Re)indexes one document. Returns its chunk count. Builds the index if there is none."""
    records = load_file(path)
    if not exists():
        rebuild()
        return meta().get("sources", {}).get(path.name, 0)
    with _lock:
        chunks, vectors = _load()
        new_vectors = _embed(records) if records else np.zeros((0, vectors.shape[1] if vectors.size else 0), dtype=np.float32)
        _check_compatible(new_vectors, vectors)
        keep = [i for i, c in enumerate(chunks) if _file_of(c) != path.name]
        kept_chunks = [chunks[i] for i in keep]
        kept_vectors = vectors[keep] if vectors.size else vectors
        if new_vectors.size:
            merged = np.vstack([kept_vectors, new_vectors]) if kept_vectors.size else new_vectors
        else:
            merged = kept_vectors
        _save(kept_chunks + records, merged, meta().get("embedder") or current_embedder())
        return len(records)


def remove_source(name: str) -> int:
    """Drops a document's chunks. Returns how many were removed."""
    if not exists():
        return 0
    with _lock:
        chunks, vectors = _load()
        keep = [i for i, c in enumerate(chunks) if _file_of(c) != name]
        removed = len(chunks) - len(keep)
        if removed:
            _save([chunks[i] for i in keep], vectors[keep], meta().get("embedder") or current_embedder())
        return removed


def chunk_count(name: str) -> Optional[int]:
    return meta().get("sources", {}).get(name)
