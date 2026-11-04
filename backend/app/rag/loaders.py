"""Which document formats the dataset accepts, and a quick readability check for uploads.

Parsing itself lives in app.rag.page_loader (the one document reader the index uses);
this module only reuses its parsers to reject an upload with no readable text before
the dataset changes.
"""
from pathlib import Path

from app.rag import page_loader

# Legacy binary .doc isn't readable without extra system tools, so it's rejected with a
# "save as .docx or PDF" message.
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".csv", ".txt", ".md"}


class UnsupportedDocument(ValueError):
    pass


def has_readable_text(path: Path) -> bool:
    """False for a DOCX, CSV or text file that yields no indexable text.

    PDFs always pass: a scanned PDF has no text layer but the index can still read it
    with OCR or visual retrieval when those are enabled.
    """
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return True
    if suffix == ".docx":
        records = page_loader._load_docx(path)
    elif suffix in (".txt", ".md"):
        records = page_loader._load_text(path)
    elif suffix == ".csv":
        records = page_loader._load_csv(path)
    else:
        raise UnsupportedDocument(f"unsupported file type '{suffix or 'none'}'")
    return any((r.get("text") or "").strip() for r in records)
