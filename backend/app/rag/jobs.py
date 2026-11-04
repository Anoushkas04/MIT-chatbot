"""The one way the chatbot index is rebuilt: a background job.

Dataset uploads, replacements and removals, the admin's Full rebuild button and the
first-start build all go through start_reindex(). A change that arrives while a build is
running queues exactly one more build, so the index always ends up reflecting the latest
documents.
"""
import datetime
import threading
import uuid
from copy import deepcopy

from app.rag.ingest import run_ingestion
from app.rag.keyword_store import clear_keyword_cache
from app.rag.store import clear_store_cache, get_store
from app.rag.visual_store import clear_visual_cache

_lock = threading.Lock()
_pending = False  # a change arrived during the running build: build again when it ends
_job = {
    "job_id": None,
    "status": "idle",
    "progress": 0,
    "message": "No reindex job has run in this process.",
    "started_at": None,
    "finished_at": None,
    "result": None,
    "error": None,
}


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _update(**values) -> None:
    with _lock:
        _job.update(values)


def _build_once() -> None:
    try:
        result = run_ingestion(lambda progress, message: _update(progress=progress, message=message))
        # Every retriever reads the index through a cache; drop them all so dense, BM25 and
        # visual search use the new documents straight away.
        clear_store_cache()
        clear_keyword_cache()
        clear_visual_cache()
        get_store()  # Validate the newly replaced files before reporting success.
        _update(status="completed", progress=100, message="RAG index replaced and loaded.", finished_at=_now(), result=result, error=None)
    except Exception as exc:
        _update(status="failed", message="Reindexing failed; the previous index remains available.", finished_at=_now(), error=str(exc))


def _run() -> None:
    global _pending
    while True:
        _build_once()
        with _lock:
            if not _pending:
                return
            _pending = False
            _job.update({"status": "running", "progress": 0, "message": "Rebuilding again for a change made during the last build.",
                         "started_at": _now(), "finished_at": None, "result": None, "error": None})


def start_reindex() -> dict:
    """Starts a rebuild, or queues one more if a build is already running."""
    global _pending
    with _lock:
        if _job["status"] in {"queued", "running"}:
            _pending = True
            return {"accepted": True, "queued": True, **deepcopy(_job)}
        job_id = uuid.uuid4().hex
        _job.update({
            "job_id": job_id, "status": "running", "progress": 0,
            "message": "Reindex job started.", "started_at": _now(),
            "finished_at": None, "result": None, "error": None,
        })
    threading.Thread(target=_run, daemon=True, name=f"rag-reindex-{job_id[:8]}").start()
    return {"accepted": True, "queued": False, **get_reindex_status()}


def get_reindex_status() -> dict:
    with _lock:
        return deepcopy(_job)
