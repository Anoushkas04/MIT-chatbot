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
    RAG_RENDER_DPI,
    VISUAL_RAG_ENABLED,
)
from app.llm import embed_texts
from app.rag.manifest import build_manifest, write_manifest
from app.rag.page_loader import load_corpus
from app.rag.visual_store import (
    VISUAL_EMBEDDINGS_PATH,
    VISUAL_MANIFEST_PATH,
    build_visual_index,
    clear_visual_cache,
)


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
            render_images=VISUAL_RAG_ENABLED,
            render_dpi=RAG_RENDER_DPI,
        )
        if not records:
            raise RuntimeError(f"No extractable text or CSV rows found in {DOCS_DIR}.")

        progress(30, f"Embedding {len(records)} text chunks")
        embeddings = embed_texts([
            f"Source: {record.get('source_file') or record.get('source', '')}\n{record['text']}"
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
        manifest["page_count"] = len(pages)
        manifest["text_chunk_count"] = len(records)
        manifest["scanned_page_count"] = sum(not page.get("text") for page in pages)
        write_manifest(temp_path / "manifest.json", manifest)

        progress(65, "Replacing the validated text index")
        for name in ("embeddings.npy", "chunks.json", "pages.json", "manifest.json"):
            (temp_path / name).replace(DATA_DIR / name)

        visual_result = None
        if VISUAL_RAG_ENABLED:
            target_images = DATA_DIR / "page_images"
            if target_images.exists():
                shutil.rmtree(target_images)
            shutil.move(str(image_dir), str(target_images))
            VISUAL_EMBEDDINGS_PATH.unlink(missing_ok=True)
            VISUAL_MANIFEST_PATH.unlink(missing_ok=True)
            clear_visual_cache()
            progress(70, f"Building visual index with {COLVISION_MODEL}")
            visual_result = build_visual_index(
                pages,
                target_images,
                lambda percent, message: progress(70 + int(percent * 0.29), message),
            )

    progress(100, f"Indexed {len(records)} text chunks across {len(pages)} PDF pages")
    return {
        "chunk_count": len(records),
        "document_count": manifest["file_count"],
        "page_count": len(pages),
        "scanned_page_count": manifest["scanned_page_count"],
        "visual": visual_result,
    }


def main():
    print(json.dumps(run_ingestion(), indent=2))


if __name__ == "__main__":
    main()
