import csv
from pathlib import Path

import pymupdf as fitz

from app.rag.chunker import chunk_text
from app.rag.manifest import document_id
from app.rag.metadata import infer_document_metadata, normalize_department

# Files kept in the documents folder that aren't campus knowledge: the project's own
# synopsis describes the chatbot, so citing it as an MIT source would be wrong.
NOT_KNOWLEDGE = {"minor_project_synopsys.pdf"}


def load_corpus(
    docs_dir: Path,
    image_dir: Path,
    *,
    render_images: bool,
    render_dpi: int = 144,
    visual_scope: str = "scanned",
) -> tuple[list[dict], list[dict]]:
    if visual_scope not in {"scanned", "all"}:
        raise ValueError("visual_scope must be 'scanned' or 'all'.")
    pages: list[dict] = []
    chunks: list[dict] = []
    if render_images:
        image_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(
        item for item in docs_dir.iterdir()
        if item.is_file() and not item.name.startswith(".") and item.name not in NOT_KNOWLEDGE
    ):
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            pdf_pages, pdf_chunks = _load_pdf(path, image_dir, render_images, render_dpi, visual_scope)
            pages.extend(pdf_pages)
            chunks.extend(pdf_chunks)
        elif suffix == ".docx":
            chunks.extend(_load_docx(path))
        elif suffix in (".txt", ".md"):
            chunks.extend(_load_text(path))
        elif suffix == ".csv" or _looks_like_csv(path):
            chunks.extend(_load_csv(path))
    return pages, chunks


def _load_pdf(
    path: Path,
    image_dir: Path,
    render_images: bool,
    render_dpi: int,
    visual_scope: str,
) -> tuple[list[dict], list[dict]]:
    doc_id = document_id(path)
    page_records: list[dict] = []
    chunk_records: list[dict] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document):
            page_number = page_index + 1
            page_id = f"{doc_id}-p{page_number:04d}"
            text = page.get_text("text").strip()
            metadata = infer_document_metadata(path.name, text)
            image_rel = None
            should_render = render_images and (visual_scope == "all" or not text)
            if should_render:
                image_name = f"{page_id}.png"
                image_path = image_dir / image_name
                pixmap = page.get_pixmap(dpi=render_dpi, alpha=False)
                pixmap.save(image_path)
                image_rel = f"page_images/{image_name}"
            page_records.append({
                "id": page_id,
                "page_id": page_id,
                "document_id": doc_id,
                "source": path.name,
                "page_number": page_number,
                "text": text,
                "image_path": image_rel,
                "record_type": "pdf_page",
                "is_scanned": not bool(text),
                **metadata,
            })
            for chunk_index, value in enumerate(chunk_text(text)):
                chunk_records.append({
                    "id": f"{page_id}-c{chunk_index:03d}",
                    "page_id": page_id,
                    "document_id": doc_id,
                    "source": path.name,
                    "source_file": path.name,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "text": value,
                    "image_path": image_rel,
                    "record_type": "pdf_chunk",
                    **metadata,
                })
    return page_records, chunk_records


def _load_docx(path: Path) -> list[dict]:
    from docx import Document

    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    # Tables carry most of the structured info in campus documents (timetables, fees).
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(dict.fromkeys(cells)))  # merged cells repeat; keep one
    return _text_chunks(path, "\n\n".join(parts), "docx_chunk")


def _load_text(path: Path) -> list[dict]:
    return _text_chunks(path, path.read_text(encoding="utf-8", errors="ignore"), "text_chunk")


def _text_chunks(path: Path, full_text: str, record_type: str) -> list[dict]:
    doc_id = document_id(path)
    metadata = infer_document_metadata(path.name, full_text)
    records = []
    for index, value in enumerate(chunk_text(full_text)):
        records.append({
            "id": f"{doc_id}-r{index + 1:05d}",
            "document_id": doc_id,
            "source": path.name,
            "source_file": path.name,
            "page_number": None,
            "chunk_index": index,
            "text": value,
            "image_path": None,
            "record_type": record_type,
            **metadata,
        })
    return records


def _looks_like_csv(path: Path) -> bool:
    try:
        if path.read_bytes()[:4] == b"%PDF":
            return False
        return "," in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines()[0]
    except (OSError, IndexError):
        return False


def _load_csv(path: Path) -> list[dict]:
    doc_id = document_id(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    records = []
    for index, row in enumerate(rows):
        text = row.get("text") or _row_to_sentence(row)
        if not text.strip():
            continue
        source = row.get("source") or path.name
        metadata = infer_document_metadata(source, text)
        department_value = row.get("department") or row.get("Department")
        department_code, department = normalize_department(department_value)
        if department_value:
            metadata["department_code"] = department_code
            metadata["department"] = department
        if row.get("document_type"):
            metadata["document_type"] = row["document_type"]
        records.append({
            "id": f"{doc_id}-r{index + 1:05d}",
            "document_id": doc_id,
            "source": source,
            "source_file": path.name,
            "page_number": None,
            "chunk_index": index,
            "text": text.strip(),
            "image_path": None,
            "record_type": "csv_row",
            "designation": row.get("designation") or row.get("Title"),
            "email": row.get("email") or row.get("Mail ID"),
            "cabin": row.get("cabin_no") or row.get("Cabin"),
            **metadata,
        })
    return records


def _row_to_sentence(row: dict) -> str:
    parts = [f"{key.strip()}: {str(value).strip()}" for key, value in row.items() if value and str(value).strip()]
    return ". ".join(parts) + ("." if parts else "")
