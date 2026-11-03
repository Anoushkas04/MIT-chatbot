import sys

# Standalone entrypoint (run via `python -m app.rag.ingest`) — doesn't go through
# app.main, so it needs its own UTF-8 stdout guard for the emoji in fallback logs.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from app.config import DATA_DIR, DOCS_DIR
from app.rag import index


def main():
    print(f"Loading and embedding documents from {DOCS_DIR} ...")
    count = index.rebuild()
    if not count:
        print("No documents found - nothing to ingest.")
        return
    print(f"Saved {count} chunks to {DATA_DIR} ({index.current_embedder()})")


if __name__ == "__main__":
    main()
