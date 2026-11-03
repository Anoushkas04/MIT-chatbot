import json
import sys

import numpy as np

# Standalone entrypoint (run via `python -m app.rag.ingest`) — doesn't go through
# app.main, so it needs its own UTF-8 stdout guard for the emoji in fallback logs.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from app.config import DATA_DIR, DOCS_DIR
from app.llm import embed_texts
from app.rag.loaders import load_documents


def main():
    print(f"Loading documents from {DOCS_DIR}")
    records = load_documents(DOCS_DIR)
    if not records:
        print("No documents found - nothing to ingest.")
        return

    texts = [r["text"] for r in records]
    print(f"Embedding {len(texts)} chunks via Gemini ({DATA_DIR.name}/)...")
    embeddings = embed_texts(texts)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    np.save(DATA_DIR / "embeddings.npy", np.array(embeddings, dtype=np.float32))
    (DATA_DIR / "chunks.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(records)} chunks to {DATA_DIR}")


if __name__ == "__main__":
    main()
