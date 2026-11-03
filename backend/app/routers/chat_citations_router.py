import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import DATA_DIR, DOCS_DIR, RAG_RENDER_DPI


router = APIRouter(prefix="/api/search", tags=["2. AI Copilot & RAG Retrieval"])


@router.get("/source/{filename}", summary="Open a chatbot citation source")
def get_chat_source(filename: str):
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid source filename.")
    path = (DOCS_DIR / filename).resolve()
    docs_root = DOCS_DIR.resolve()
    if docs_root not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="Source document not found.")
    return FileResponse(path, filename=path.name)


@router.get("/page/{document_id}/{page_number}", summary="Open a cited chatbot PDF page")
def get_chat_cited_page(document_id: str, page_number: int):
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
