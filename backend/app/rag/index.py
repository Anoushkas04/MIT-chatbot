"""Adapter so the admin dataset manager (routers/admin_dataset.py) can add, replace or
remove documents without knowing about the hybrid RAG pipeline's internals.

The pipeline's chunking is page-aware (and optionally OCR/visual), so there's no cheap
single-file update to do — every add/replace/remove here triggers a full corpus rebuild
via app.rag.ingest.run_ingestion. Admin uploads are rare, manual actions, so paying for
a full rebuild (a minute or two) in exchange for one consistent index schema — with real
page citations for every document, not just ones added via `python -m app.rag.ingest` —
beats maintaining two incompatible RAG systems side by side.
"""
import json
import threading
from pathlib import Path
from typing import Optional

from app.config import DATA_DIR
from app.rag import jobs
from app.rag.ingest import run_ingestion
from app.rag.loaders import SUPPORTED_EXTENSIONS, UnsupportedDocument
from app.rag.store import clear_store_cache, get_store

CHUNKS = DATA_DIR / "chunks.json"
EMBEDDINGS = DATA_DIR / "embeddings.npy"
MANIFEST = DATA_DIR / "manifest.json"

_lock = threading.Lock()


class NeedsFullRebuild(RuntimeError):
    """Kept for callers that still catch it — every write here already does a full
    rebuild, so this adapter never actually raises it."""


def __getattr__(name: str):
    # Lets `index.rebuild_state` (read as a plain attribute by admin_dataset.py) always
    # reflect the live background-job status from app.rag.jobs instead of a stale snapshot.
    if name == "rebuild_state":
        return _rebuild_state()
    raise AttributeError(name)


def _rebuild_state() -> dict:
    j = jobs.get_reindex_status()
    result = j.get("result") or {}
    return {
        "running": j["status"] in ("queued", "running"),
        "started_at": j["started_at"],
        "finished_at": j["finished_at"],
        "error": j["error"],
        "chunks": result.get("chunk_count"),
    }


def exists() -> bool:
    return CHUNKS.exists() and EMBEDDINGS.exists()


def meta() -> dict:
    if not MANIFEST.exists():
        return {}
    try:
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    sources: dict = {}
    if CHUNKS.exists():
        try:
            for c in json.loads(CHUNKS.read_text(encoding="utf-8")):
                key = c.get("file") or c.get("source")
                if key:
                    sources[key] = sources.get(key, 0) + 1
        except (OSError, ValueError):
            pass
    return {
        "embedder": m.get("text_embedding_model"),
        "built_at": m.get("created_at"),
        "total_chunks": m.get("text_chunk_count"),
        "sources": sources,
    }


def current_embedder() -> str:
    from app.config import EMBEDDING_MODEL, GEMINI_API_KEY
    from app.llm import is_valid_key
    return f"gemini:{EMBEDDING_MODEL}" if is_valid_key(GEMINI_API_KEY) else "local-hash"


def chunk_count(name: str) -> Optional[int]:
    return meta().get("sources", {}).get(name)


def rebuild() -> int:
    """Re-reads every document in DOCS_DIR and rebuilds the whole index. Blocks until done."""
    with _lock:
        result = run_ingestion()
        clear_store_cache()
        get_store()  # validate the new index before reporting success
        return result["chunk_count"]


def rebuild_in_background() -> bool:
    """Starts a full rebuild on a thread; False if one is already running."""
    return jobs.start_reindex()["accepted"]


def upsert_file(path: Path) -> int:
    """(Re)indexes one document by rebuilding the whole corpus. Returns its chunk count."""
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise UnsupportedDocument(f"unsupported file type '{path.suffix or 'none'}'")
    rebuild()
    return chunk_count(path.name) or 0


def remove_source(name: str) -> int:
    """Drops a document's chunks by rebuilding (the caller deletes the file from DOCS_DIR
    first). Returns how many chunks it had."""
    before = chunk_count(name) or 0
    if before:
        rebuild()
    return before
