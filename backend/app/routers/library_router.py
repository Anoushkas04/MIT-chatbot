"""Student-facing access to the official dataset the admins manage: search across the
indexed documents, the document list, and downloads. Replaces the old hard-coded
/api/search results, so what admins upload is what students find.
"""
import datetime
import mimetypes

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app import models
from app.config import DOCS_DIR
from app.llm import embed_query
from app.rag import index
from app.rag.loaders import SUPPORTED_EXTENSIONS
from app.rag.page_loader import NOT_KNOWLEDGE
from app.routers.admin_dataset import _doc_path, _human
from app.routers.auth_router import get_current_user

router = APIRouter(tags=["10. Global Intelligent Search"])

MIN_SCORE = 0.15  # below this a vector match is noise (true for both Gemini and local embeddings)


def _title(name: str) -> str:
    stem = name.rsplit(".", 1)[0]
    return " ".join(stem.replace("_", " ").split())


@router.get("/api/search", summary="Search the official documents the chatbot answers from")
def search(q: str = Query(..., min_length=2, max_length=200), me: models.User = Depends(get_current_user)):
    if not index.exists():
        return {"results": [], "indexed": False}
    from app.rag.store import get_store

    try:
        store = get_store()
        hits = store.search(embed_query(q, store.embedder), raw_query=q, k=20)
    except Exception:
        return {"results": [], "indexed": False}
    best: dict = {}  # one result per document file, keeping its best-matching chunk
    for h in hits:
        if h["score"] < MIN_SCORE:
            continue
        f = h.get("source_file") or h.get("file") or h["source"]  # file name; "source" may be a CSV label
        if f not in best or h["score"] > best[f]["score"]:
            best[f] = h
    results = [
        {
            "source": f,  # the file name, used for downloads
            # A CSV may carry a friendlier citation label than its file name.
            "title": h["source"] if h["source"] != f else _title(f),
            "type": f.rsplit(".", 1)[-1].upper() if "." in f else "DOC",
            "snippet": " ".join(h["text"].split())[:260],
            "score": round(h["score"], 3),
            "downloadable": (DOCS_DIR / f).is_file(),
        }
        for f, h in best.items()
    ]
    results.sort(key=lambda r: r["score"], reverse=True)
    return {"results": results[:8], "indexed": True}


@router.get("/api/documents", summary="Official documents in the dataset (readable formats only)")
def list_documents(me: models.User = Depends(get_current_user)):
    out = []
    if DOCS_DIR.exists():
        for p in sorted(DOCS_DIR.iterdir(), key=lambda x: x.name.lower()):
            if (
                not p.is_file() or p.name.startswith(".")
                or p.suffix.lower() not in SUPPORTED_EXTENSIONS or p.name in NOT_KNOWLEDGE
            ):
                continue
            stat = p.stat()
            out.append({
                "name": p.name,
                "title": _title(p.name),
                "type": p.suffix.lstrip(".").upper(),
                "size": _human(stat.st_size),
                "updated": datetime.datetime.utcfromtimestamp(stat.st_mtime).strftime("%b %Y"),
            })
    return {"documents": out}


@router.get("/api/documents/{name}/download", summary="Download an official document")
def download(name: str, me: models.User = Depends(get_current_user)):
    path = _doc_path(name)  # rejects paths and anything outside the documents folder
    if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=404, detail="Document not found.")
    media = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media, filename=path.name)
