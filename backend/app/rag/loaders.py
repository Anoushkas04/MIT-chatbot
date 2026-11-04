import csv
from pathlib import Path

from pypdf import PdfReader

from app.rag.chunker import chunk_text


# Formats the admin dataset manager accepts. Legacy binary .doc isn't readable without
# extra system tools, so it's rejected with a "save as .docx or PDF" message.
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".csv", ".txt", ".md"}


class UnsupportedDocument(ValueError):
    pass


def load_documents(docs_dir: Path) -> list[dict]:
    records = []
    for path in sorted(docs_dir.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        try:
            records.extend(load_file(path))
        except UnsupportedDocument as e:
            print(f"  skipping {path.name}: {e}")
    return records


def load_file(path: Path) -> list[dict]:
    """Chunks one document. Raises UnsupportedDocument for formats we can't read.

    Each record's "file" is the document's file name, which the index uses to replace or
    remove a document's chunks. "source" is the citation label, which a CSV may override
    with its own source column.
    """
    return [{**r, "file": path.name} for r in _load_any(path)]


def _load_any(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf(path)
    if suffix == ".docx":
        return _load_docx(path)
    if suffix in (".txt", ".md"):
        return [{"text": c, "source": path.name, "document_type": "text"} for c in chunk_text(path.read_text(encoding="utf-8", errors="ignore"))]
    if suffix == ".csv" or (suffix == "" and _looks_like_csv(path)):
        return _load_csv(path)
    if suffix == ".doc":
        raise UnsupportedDocument("old Word .doc files aren't supported; save it as .docx or PDF")
    raise UnsupportedDocument(f"unsupported file type '{suffix or 'none'}'")


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
    return [{"text": c, "source": path.name, "document_type": "docx"} for c in chunk_text("\n\n".join(parts))]


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
