import datetime
import threading
import uuid
from copy import deepcopy

from app.rag.ingest import run_ingestion
from app.rag.store import clear_store_cache, get_store
from app.rag.keyword_store import clear_keyword_cache
from app.rag.visual_store import clear_visual_cache

_lock = threading.Lock()
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


def _run(job_id: str) -> None:
    try:
        result = run_ingestion(lambda progress, message: _update(progress=progress, message=message))
        clear_store_cache()
        clear_keyword_cache()
        clear_visual_cache()
        get_store()  # Validate the newly replaced files before reporting success.
        _update(
            status="completed", progress=100, message="RAG index replaced and loaded.",
            finished_at=_now(), result=result,
        )
    except Exception as exc:
        _update(
            status="failed", message="Reindexing failed; the previous index remains available.",
            finished_at=_now(), error=str(exc),
        )


def start_reindex() -> dict:
    with _lock:
        if _job["status"] in {"queued", "running"}:
            return {"accepted": False, **deepcopy(_job)}
        job_id = uuid.uuid4().hex
        _job.update({
            "job_id": job_id, "status": "running", "progress": 0,
            "message": "Reindex job queued.", "started_at": _now(),
            "finished_at": None, "result": None, "error": None,
        })
    threading.Thread(target=_run, args=(job_id,), daemon=True, name=f"rag-reindex-{job_id[:8]}").start()
    return {"accepted": True, **get_reindex_status()}


def get_reindex_status() -> dict:
    with _lock:
        return deepcopy(_job)
