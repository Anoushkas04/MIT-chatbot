import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from app.config import (
    COLVISION_MODEL,
    DATA_DIR,
    DOCS_DIR,
    EMBEDDING_MODEL,
    LOCAL_OCR_ENABLED,
    OCR_CACHE_DIR,
    OCR_MAX_IMAGE_EDGE,
    OCR_MIN_CONFIDENCE,
    RAG_RENDER_DPI,
    VISUAL_RAG_ENABLED,
    VISUAL_RAG_SCOPE,
)
from app.llm import embed_texts
from app.rag.chunker import chunk_text
from app.rag.local_ocr import clear_ocr_engine_cache, extract_page
from app.rag.manifest import build_manifest, write_manifest
from app.rag.page_loader import load_corpus
from app.rag.visual_store import (
    VISUAL_EMBEDDINGS_PATH,
    VISUAL_MANIFEST_PATH,
    build_visual_index,
    clear_visual_cache,
)


def _ocr_scanned_pages(
    pages: list[dict],
    image_dir: Path,
    progress,
) -> tuple[list[dict], list[dict]]:
    scanned_pages = [
        page for page in pages
        if page.get("is_scanned") and page.get("image_path")
    ]
    if not LOCAL_OCR_ENABLED or not scanned_pages:
        return [], []

    records: list[dict] = []
    calendar_events: list[dict] = []
    total = len(scanned_pages)
    for page_index, page in enumerate(scanned_pages, start=1):
        image_path = image_dir / Path(page["image_path"]).name
        progress(
            8 + int((page_index - 1) / total * 24),
            f"Running local OCR on scanned page {page_index}/{total}: {page['source']}",
        )
        extracted = extract_page(
            image_path,
            page,
            OCR_CACHE_DIR,
            min_confidence=OCR_MIN_CONFIDENCE,
            max_image_edge=OCR_MAX_IMAGE_EDGE,
        )
        page["text"] = extracted.get("text", "")
        page["extraction_method"] = extracted.get("engine", "local_ocr")
        page["ocr_confidence"] = extracted.get("average_confidence", 0.0)
        page["ocr_line_count"] = extracted.get("line_count", 0)
        page["ocr_segment_count"] = len(extracted.get("segments", []))
        page["calendar_event_count"] = len(extracted.get("calendar_events", []))
        calendar_events.extend(extracted.get("calendar_events", []))

        record_index = 0
        for segment_index, segment in enumerate(extracted.get("segments", [])):
            segment_text = segment.get("text", "").strip()
            if not segment_text:
                continue
            values = chunk_text(segment_text)
            if not values and len(segment_text) >= 20:
                values = [segment_text]
            for value in values:
                segment_metadata = segment.get("metadata", {})
                records.append({
                    "id": f"{page['id']}-o{segment_index:03d}-c{record_index:03d}",
                    "page_id": page["id"],
                    "document_id": page["document_id"],
                    "source": page["source"],
                    "page_number": page["page_number"],
                    "chunk_index": record_index,
                    "segment_index": segment_index,
                    "segment_title": segment.get("title"),
                    "text": value,
                    "image_path": page.get("image_path"),
                    "record_type": "ocr_chunk",
                    "extraction_method": extracted.get("engine", "local_ocr"),
                    "ocr_confidence": extracted.get("average_confidence", 0.0),
                    "department_code": page.get("department_code"),
                    "department": page.get("department"),
                    "programme": page.get("programme"),
                    "academic_year": page.get("academic_year"),
                    "semester": page.get("semester"),
                    "document_type": page.get("document_type", "document"),
                    **segment_metadata,
                })
                record_index += 1
    return records, calendar_events


def _retrieval_context(record: dict) -> str:
    values = [
        f"Document title: {record.get('source_file') or record.get('source', '')}",
        f"Document type: {record.get('document_type', 'document')}",
    ]
    if record.get("department_code") or record.get("department"):
        values.append(
            f"Department: {record.get('department_code') or ''} {record.get('department') or ''}".strip()
        )
    if record.get("academic_year"):
        values.append(f"Academic year: {record['academic_year']}")
    if record.get("semester"):
        values.append(f"Semester: {record['semester']}")
    if record.get("segment_title"):
        values.append(f"Section: {record['segment_title']}")
    if record.get("designation"):
        values.append(f"Faculty designation: {record['designation']}")
    if record.get("email"):
        values.append(f"Faculty email: {record['email']}")
    if record.get("cabin"):
        values.append(f"Faculty cabin: {record['cabin']}")
    if str(record.get("source_file", "")).lower() == "mit_manipal_faculty.csv":
        values.append(
            "Institution-wide faculty directory covering all departments, searchable by department and designation"
        )
    if (
        record.get("page_number") == 1
        and record.get("document_type") in {"curriculum", "syllabus"}
    ):
        values.append("Overview, programme curriculum, course list, and subjects offered")
    return ". ".join(values) + "."


def run_ingestion(progress_callback=None) -> dict:
    progress = progress_callback or (lambda percent, message: None)
    progress(2, f"Inventorying documents from {DOCS_DIR}")
    manifest = build_manifest(
        DOCS_DIR,
        text_embedding_model=EMBEDDING_MODEL,
        visual_model=COLVISION_MODEL,
        visual_enabled=VISUAL_RAG_ENABLED,
    )
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=DATA_DIR) as temp_dir:
        temp_path = Path(temp_dir)
        image_dir = temp_path / "page_images"
        progress(5, "Extracting page text and metadata")
        pages, records = load_corpus(
            DOCS_DIR,
            image_dir,
            render_images=VISUAL_RAG_ENABLED or LOCAL_OCR_ENABLED,
            render_dpi=RAG_RENDER_DPI,
            visual_scope=VISUAL_RAG_SCOPE,
        )
        ocr_records, calendar_events = _ocr_scanned_pages(pages, image_dir, progress)
        records.extend(ocr_records)
        if not records:
            raise RuntimeError(f"No extractable text or CSV rows found in {DOCS_DIR}.")
        for record in records:
            record["retrieval_text"] = _retrieval_context(record)

        progress(35, f"Embedding {len(records)} text chunks")
        embeddings = embed_texts([
            "\n".join(part for part in (
                record["retrieval_text"],
                record["text"],
            ) if part)
            for record in records
        ])
        embeddings_array = np.asarray(embeddings, dtype=np.float32)
        if len(embeddings_array) != len(records):
            raise RuntimeError("Embedding provider returned an unexpected number of vectors.")

        np.save(temp_path / "embeddings.npy", embeddings_array)
        (temp_path / "chunks.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (temp_path / "pages.json").write_text(
            json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (temp_path / "calendar_events.json").write_text(
            json.dumps(calendar_events, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        manifest["page_count"] = len(pages)
        manifest["text_chunk_count"] = len(records)
        manifest["scanned_page_count"] = sum(bool(page.get("is_scanned")) for page in pages)
        manifest["ocr_page_count"] = sum(bool(page.get("extraction_method")) for page in pages)
        manifest["ocr_chunk_count"] = len(ocr_records)
        manifest["calendar_event_count"] = len(calendar_events)
        manifest["visual_scope"] = VISUAL_RAG_SCOPE
        manifest["visual_page_count"] = sum(bool(page.get("image_path")) for page in pages)
        write_manifest(temp_path / "manifest.json", manifest)

        progress(65, "Replacing the validated text index")
        for name in (
            "embeddings.npy",
            "chunks.json",
            "pages.json",
            "calendar_events.json",
            "manifest.json",
        ):
            (temp_path / name).replace(DATA_DIR / name)

        visual_result = None
        target_images = DATA_DIR / "page_images"
        if image_dir.exists():
            if target_images.exists():
                shutil.rmtree(target_images)
            shutil.move(str(image_dir), str(target_images))
        if VISUAL_RAG_ENABLED:
            VISUAL_EMBEDDINGS_PATH.unlink(missing_ok=True)
            VISUAL_MANIFEST_PATH.unlink(missing_ok=True)
            clear_visual_cache()
            progress(70, f"Building visual index with {COLVISION_MODEL}")
            visual_result = build_visual_index(
                pages,
                target_images,
                lambda percent, message: progress(70 + int(percent * 0.29), message),
            )
        clear_ocr_engine_cache()

    progress(100, f"Indexed {len(records)} text chunks across {len(pages)} PDF pages")
    return {
        "chunk_count": len(records),
        "document_count": manifest["file_count"],
        "page_count": len(pages),
        "scanned_page_count": manifest["scanned_page_count"],
        "ocr_page_count": manifest["ocr_page_count"],
        "ocr_chunk_count": manifest["ocr_chunk_count"],
        "calendar_event_count": manifest["calendar_event_count"],
        "visual": visual_result,
    }


def main():
    print(json.dumps(run_ingestion(), indent=2))


if __name__ == "__main__":
    main()
