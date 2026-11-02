import math
import json
import re
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app import models
from app.config import DATA_DIR, DOCS_DIR, RAG_RENDER_DPI
from app.database import SessionLocal
from app.rag.store import get_store

router = APIRouter(prefix="/api/search", tags=["10. Global Intelligent Search"])


def _score(query: str, *values: str) -> float:
    words = {word for word in re.findall(r"\w+", query.lower()) if len(word) > 1}
    if not words:
        return 0.5
    haystack = " ".join(value or "" for value in values).lower()
    matched = sum(1 for word in words if word in haystack)
    return round(matched / len(words), 4)


def _matches_category(item: dict, category: str) -> bool:
    normalized = (category or "all").lower()
    return normalized == "all" or normalized == item["source_type"] or normalized in item["category"].lower()


@router.get("/source/{filename}", summary="Open an indexed public source document")
def get_source(filename: str):
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid source filename.")
    path = (DOCS_DIR / filename).resolve()
    docs_root = DOCS_DIR.resolve()
    if docs_root not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="Source document not found.")
    return FileResponse(path, filename=path.name)


@router.get("/page/{document_id}/{page_number}", summary="Open a cited PDF page")
def get_cited_page(document_id: str, page_number: int):
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", document_id) or page_number < 1:
        raise HTTPException(status_code=400, detail="Invalid citation location.")
    pages_path = DATA_DIR / "pages.json"
    try:
        pages = json.loads(pages_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise HTTPException(status_code=503, detail="The page index is not ready.")

    record = next(
        (page for page in pages if page.get("document_id") == document_id and page.get("page_number") == page_number),
        None,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Cited page not found.")

    image_path = DATA_DIR / "page_images" / f"{record['id']}.png"
    if not image_path.is_file():
        source_path = (DOCS_DIR / Path(str(record.get("source", ""))).name).resolve()
        if DOCS_DIR.resolve() not in source_path.parents or not source_path.is_file():
            raise HTTPException(status_code=404, detail="Citation source document not found.")
        image_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import pymupdf as fitz
            with fitz.open(source_path) as document:
                if page_number > document.page_count:
                    raise HTTPException(status_code=404, detail="Cited page not found in source.")
                pixmap = document[page_number - 1].get_pixmap(dpi=RAG_RENDER_DPI, alpha=False)
                pixmap.save(image_path)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Could not render cited page: {exc}")
    return FileResponse(image_path, media_type="image/png", filename=f"{record['source']}-page-{page_number}.png")


@router.get("", summary="Execute global multi-domain search over live campus sources")
def perform_search(
    q: Optional[str] = None,
    category: str = "all",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    query = (q or "").strip()
    results: list[dict] = []
    db = SessionLocal()
    try:
        events = db.query(models.AcademicEvent).filter(models.AcademicEvent.status == "published").all()
        for event in events:
            relevance = _score(query, event.title, event.description or "", event.category, event.source)
            if query and relevance == 0:
                continue
            results.append({
                "id": f"event-{event.id}", "title": event.title, "category": "Events",
                "source_type": "events", "badge": "Official event",
                "snippet": event.description or f"Scheduled for {event.start_datetime.isoformat()}.",
                "link_target": "/api/academic/timeline", "relevance": relevance, "source": event.source,
            })

        posts = db.query(models.StudentPost).order_by(models.StudentPost.created_at.desc()).limit(200).all()
        for post in posts:
            relevance = _score(query, post.title, post.content, post.sub_community, post.tag)
            if query and relevance == 0:
                continue
            results.append({
                "id": f"community-{post.id}", "title": post.title, "category": "Community",
                "source_type": "community", "badge": "Verified community" if post.verified else "Community post",
                "snippet": post.content[:320], "link_target": f"/api/posts?category={quote(post.sub_community)}",
                "relevance": relevance, "source": post.sub_community,
            })
    finally:
        db.close()

    try:
        store = get_store()
        seen_sources: set[str] = set()
        ranked_chunks = []
        for index, chunk in enumerate(store.chunks):
            source = str(chunk.get("source", "Unknown source"))
            relevance = _score(query, chunk.get("text", ""), source)
            if query and relevance == 0:
                continue
            ranked_chunks.append((relevance, index, chunk, source))
        for relevance, index, chunk, source in sorted(ranked_chunks, reverse=True)[:100]:
            source_name = Path(source).name
            key = source_name.lower()
            if key in seen_sources:
                continue
            seen_sources.add(key)
            is_faculty = "faculty" in key or "cabin" in key
            source_file = source_name
            if not (DOCS_DIR / source_file).is_file() and is_faculty:
                source_file = "mit_manipal_faculty.csv"
            source_link = (
                f"/api/search/source/{quote(source_file)}"
                if (DOCS_DIR / source_file).is_file()
                else f"/api/search?q={quote(source_name)}"
            )
            results.append({
                "id": f"document-{index}", "title": source_name,
                "category": "Faculty" if is_faculty else "Documents",
                "source_type": "faculty" if is_faculty else "documents",
                "badge": "Indexed faculty directory" if is_faculty else "Indexed document",
                "snippet": str(chunk.get("text", ""))[:320],
                "link_target": source_link,
                "relevance": relevance, "source": source_name,
            })
    except (FileNotFoundError, ValueError, OSError):
        pass

    filtered = [item for item in results if _matches_category(item, category)]
    filtered.sort(key=lambda item: item["relevance"], reverse=True)
    total = len(filtered)
    offset = (page - 1) * page_size
    page_results = filtered[offset:offset + page_size]
    return {
        "query": query, "category": category, "page": page, "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total else 0,
        "total_results": total,
        "official_count": sum(1 for item in filtered if item["source_type"] != "community"),
        "community_count": sum(1 for item in filtered if item["source_type"] == "community"),
        "results": page_results,
    }
