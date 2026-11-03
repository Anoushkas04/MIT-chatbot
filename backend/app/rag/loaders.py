import csv
from pathlib import Path

from pypdf import PdfReader

from app.rag.chunker import chunk_text


def load_documents(docs_dir: Path) -> list[dict]:
    records = []
    for path in sorted(docs_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".pdf":
            records.extend(_load_pdf(path))
        elif path.suffix.lower() == ".csv" or _looks_like_csv(path):
            records.extend(_load_csv(path))
        else:
            print(f"  skipping unsupported file: {path.name}")
    return records


def _looks_like_csv(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            if f.read(4) == b"%PDF":
                return False
        with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
            first_line = f.readline()
        return "," in first_line
    except OSError:
        return False


def _load_pdf(path: Path) -> list[dict]:
    reader = PdfReader(str(path))
    full_text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return [{"text": c, "source": path.name, "document_type": "pdf"} for c in chunk_text(full_text)]


def _load_csv(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return []

    if "text" in rows[0]:
        return [
            {
                "text": row["text"],
                "source": row.get("source") or path.name,
                "document_type": row.get("document_type") or "csv",
            }
            for row in rows
        ]

    return [{"text": _row_to_sentence(row), "source": path.name, "document_type": "csv"} for row in rows]


def _row_to_sentence(row: dict) -> str:
    parts = [f"{key.strip()}: {value.strip()}" for key, value in row.items() if value and value.strip()]
    return ". ".join(parts) + "."
