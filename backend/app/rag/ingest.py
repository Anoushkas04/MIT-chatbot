import json
import sys
import tempfile
from pathlib import Path

import numpy as np

# Standalone entrypoint (run via `python -m app.rag.ingest`) — doesn't go through
# app.main, so it needs its own UTF-8 stdout guard for the emoji in fallback logs.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from app.config import DATA_DIR, DOCS_DIR
from app.llm import embed_texts
from app.rag.loaders import load_documents


def run_ingestion(progress_callback=None) -> dict:
    progress = progress_callback or (lambda percent, message: None)
    progress(5, f"Loading documents from {DOCS_DIR}")
    print(f"Loading documents from {DOCS_DIR}")
    records = load_documents(DOCS_DIR)
    if not records:
        raise RuntimeError(f"No supported documents found in {DOCS_DIR}.")

    texts = [r["text"] for r in records]
    progress(35, f"Embedding {len(texts)} chunks")
    print(f"Embedding {len(texts)} chunks via Gemini ({DATA_DIR.name}/)...")
    embeddings = embed_texts(texts)

    embeddings_array = np.array(embeddings, dtype=np.float32)
    if len(embeddings_array) != len(records):
        raise RuntimeError("Embedding provider returned an unexpected number of vectors.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    progress(85, "Replacing the index atomically")
    with tempfile.TemporaryDirectory(dir=DATA_DIR) as temp_dir:
        temp_path = Path(temp_dir)
        np.save(temp_path / "embeddings.npy", embeddings_array)
        (temp_path / "chunks.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (temp_path / "embeddings.npy").replace(DATA_DIR / "embeddings.npy")
        (temp_path / "chunks.json").replace(DATA_DIR / "chunks.json")
    progress(100, f"Indexed {len(records)} chunks")
    print(f"Saved {len(records)} chunks to {DATA_DIR}")
    return {"chunk_count": len(records), "document_count": len({r.get('source', '') for r in records})}


def main():
    run_ingestion()


if __name__ == "__main__":
    main()
