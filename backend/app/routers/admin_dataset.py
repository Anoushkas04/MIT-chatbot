"""Admin dataset manager: the documents the chatbot answers from.

Uploading, replacing or removing a file updates the chatbot index straight away and is
recorded in the audit log. Replaced and removed files are kept in data/doc_history/.
"""
import datetime
import io
import re
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app import audit, models
from app.config import DATA_DIR, DOCS_DIR
from app.database import SessionLocal
from app.rag import index
from app.rag.loaders import SUPPORTED_EXTENSIONS, has_readable_text
from app.routers.admin_router import require_admin_user
from app.routers.community_v2 import _relative

router = APIRouter(prefix="/api/admin/dataset", tags=["8. Admin Console & Operations"], dependencies=[Depends(require_admin_user)])

MAX_BYTES = 25 * 1024 * 1024
HISTORY_DIR = DATA_DIR / "doc_history"
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._()+,&'-]{0,150}$")


def _human(size: int) -> str:
    for unit in ("B", "KB", "MB"):
        if size < 1024 or unit == "MB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} MB"


def _doc_path(name: str) -> Path:
    """Resolves a file name strictly inside DOCS_DIR (no paths, no traversal)."""
    if not _SAFE_NAME.match(name or "") or name.startswith("."):
        raise HTTPException(status_code=400, detail="Invalid file name.")
    path = (DOCS_DIR / name).resolve()
    if path.parent != DOCS_DIR.resolve():
        raise HTTPException(status_code=400, detail="Invalid file name.")
    return path


def _check_content(ext: str, data: bytes) -> None:
    """Content must match the extension, so a renamed file can't slip through."""
    if ext == ".pdf" and not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="That file doesn't look like a real PDF.")
    if ext == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                if "word/document.xml" not in z.namelist():
                    raise ValueError
        except (zipfile.BadZipFile, ValueError):
            raise HTTPException(status_code=400, detail="That file doesn't look like a real Word .docx document.")
    if ext in (".csv", ".txt", ".md"):
        if b"\x00" in data[:4096]:
            raise HTTPException(status_code=400, detail="That file isn't plain text.")
        try:
            data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Text and CSV files must be saved as UTF-8.")


def _archive(path: Path) -> Path:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    dest = HISTORY_DIR / f"{stamp}__{path.name}"
    path.replace(dest)
    return dest


def _record_document(db, path: Path) -> None:
    row = db.query(models.KnowledgeDocument).filter(models.KnowledgeDocument.filename == path.name).first()
    if not row:
        row = models.KnowledgeDocument(filename=path.name)
        db.add(row)
    row.file_type = path.suffix.lstrip(".").upper()
    row.file_size = _human(path.stat().st_size)
    row.chunks_count = 0  # known once the background rebuild finishes (see list_dataset)
    row.status = "Indexing"
    row.uploaded_at = datetime.datetime.utcnow()


@router.get("", summary="Documents in the chatbot dataset, index status and community entries")
def list_dataset():
    db = SessionLocal()
    try:
        m = index.meta()
        sources = m.get("sources", {})
        history = {}
        for e in (
            db.query(models.AdminAuditLog)
            .filter(models.AdminAuditLog.action.in_(["dataset.upload", "dataset.replace"]))
            .order_by(models.AdminAuditLog.id.asc())
            .all()
        ):
            h = history.setdefault(e.target_id, {"versions": 0})
            h.update(versions=h["versions"] + 1, by=e.admin_name, action=e.action.split(".")[1], when=_relative(e.created_at))
        files = []
        if DOCS_DIR.exists():
            for p in sorted(DOCS_DIR.iterdir(), key=lambda x: x.name.lower()):
                if not p.is_file() or p.name.startswith("."):
                    continue
                stat = p.stat()
                h = history.get(p.name)
                files.append({
                    "name": p.name,
                    "type": p.suffix.lstrip(".").upper() or "?",
                    "supported": p.suffix.lower() in SUPPORTED_EXTENSIONS,
                    "size": _human(stat.st_size),
                    "modified": _relative(datetime.datetime.utcfromtimestamp(stat.st_mtime)),
                    "chunks": sources.get(p.name),
                    "version": (h["versions"] if h else 0) + 1,  # the original copy counts as v1
                    "last_change": {k: h[k] for k in ("by", "action", "when")} if h else None,
                })
        community = db.query(models.CommunityPost).filter(models.CommunityPost.in_dataset.is_(True), models.CommunityPost.deleted_at.is_(None)).count()
        return {
            "files": files,
            "index": {
                "exists": index.exists(),
                "embedder": m.get("embedder"),
                "current_embedder": index.current_embedder(),
                "built_at": m.get("built_at"),
                "total_chunks": m.get("total_chunks"),
                "rebuild": index.rebuild_state,
            },
            "community_posts_in_dataset": community,
            "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
            "max_mb": MAX_BYTES // (1024 * 1024),
        }
    finally:
        db.close()


@router.post("/upload", summary="Add a document, or replace one with replace=true (PDF, DOCX, CSV, TXT, MD)")
async def upload(file: UploadFile = File(...), replace: bool = Form(False), admin: models.User = Depends(require_admin_user)):
    name = Path(file.filename or "").name.strip()
    ext = Path(name).suffix.lower()
    if ext == ".doc":
        raise HTTPException(status_code=400, detail="Old Word .doc files aren't supported. Save it as .docx or PDF and upload again.")
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Use one of: {', '.join(sorted(SUPPORTED_EXTENSIONS))}.")
    path = _doc_path(name)
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"Files must be under {MAX_BYTES // (1024 * 1024)} MB.")
    if not data:
        raise HTTPException(status_code=400, detail="The file is empty.")
    _check_content(ext, data)
    existed = path.exists()
    if existed and not replace:
        raise HTTPException(status_code=409, detail=f'"{name}" is already in the dataset. Use Replace to upload a new version.')
    if replace and not existed:
        raise HTTPException(status_code=404, detail=f'"{name}" isn\'t in the dataset, so there\'s nothing to replace.')

    # A DOCX, CSV or text file with no text is refused here, before the dataset changes.
    # (Scanned PDFs pass: the rebuild can still read them with OCR or visual retrieval.)
    probe = HISTORY_DIR.parent / f".upload-check-{uuid.uuid4().hex}{ext}"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_bytes(data)
    try:
        readable = has_readable_text(probe)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Couldn't read that file: {e}")
    finally:
        probe.unlink(missing_ok=True)
    if not readable:
        raise HTTPException(status_code=400, detail="No readable text was found in that file. Nothing was changed.")

    archived = _archive(path) if existed else None
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    # The full-corpus rebuild runs in the background (or is queued behind one already
    # running); the Dataset page polls index.rebuild and shows the chunk count when done.
    index.rebuild_in_background()

    db = SessionLocal()
    try:
        _record_document(db, path)
        action = "dataset.replace" if existed else "dataset.upload"
        audit.record(
            db, admin, action,
            f'{"Replaced" if existed else "Added"} "{name}" ({_human(len(data))}); reindexing in the background',
            "file", name, {"size": len(data), "previous_version": archived.name if archived else None},
        )
        db.commit()
        return {"status": "replaced" if existed else "added", "name": name, "indexing": True}
    finally:
        db.close()


@router.delete("/files/{name}", summary="Remove a document from the dataset (kept in history)")
def remove(name: str, admin: models.User = Depends(require_admin_user)):
    path = _doc_path(name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="That file isn't in the dataset.")
    removed = index.chunk_count(name) or 0
    # Move the file out BEFORE rebuilding, or the rebuild re-indexes the document being removed.
    archived = _archive(path)
    index.rebuild_in_background()
    db = SessionLocal()
    try:
        row = db.query(models.KnowledgeDocument).filter(models.KnowledgeDocument.filename == name).first()
        if row:
            db.delete(row)
        audit.record(db, admin, "dataset.remove", f'Removed "{name}" ({removed} chunks)', "file", name, {"archived_as": archived.name, "chunks": removed})
        db.commit()
        return {"status": "removed", "name": name, "chunks_removed": removed, "indexing": True}
    finally:
        db.close()


@router.post("/rebuild", summary="Rebuild the whole chatbot index from every document (runs in the background)")
def rebuild(admin: models.User = Depends(require_admin_user)):
    already_running = index.rebuild_state["running"]
    index.rebuild_in_background()  # queued behind the running build if there is one
    db = SessionLocal()
    try:
        audit.record(db, admin, "dataset.rebuild", "Started a full rebuild of the chatbot index", "index", None, {"embedder": index.current_embedder()})
        db.commit()
    finally:
        db.close()
    return {"status": "queued" if already_running else "started"}
