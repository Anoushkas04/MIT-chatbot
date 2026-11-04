"""Adapter between the admin dataset manager (routers/admin_dataset.py) and the hybrid RAG
pipeline. The pipeline's chunking is page-aware (and optionally OCR/visual), so there is
no cheap single-file update: every add, replace or remove starts a full rebuild in the
background via app.rag.jobs, the one rebuild path, and the admin pages poll its status.
"""
import json
from typing import Optional

from app.config import DATA_DIR
from app.llm import active_embedder
from app.rag import jobs

CHUNKS = DATA_DIR / "chunks.json"
EMBEDDINGS = DATA_DIR / "embeddings.npy"
MANIFEST = DATA_DIR / "manifest.json"


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
                # source_file is the file name; "source" can be a CSV's own citation label.
                key = c.get("source_file") or c.get("file") or c.get("source")
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
    return active_embedder()


def chunk_count(name: str) -> Optional[int]:
    return meta().get("sources", {}).get(name)


def rebuild_in_background() -> bool:
    """Starts a full rebuild in the background, or queues one if a build is running."""
    return jobs.start_reindex()["accepted"]
