import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 2


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def document_id(path: Path) -> str:
    return hashlib.sha256(path.name.encode("utf-8")).hexdigest()[:16]


def build_manifest(docs_dir: Path, *, text_embedding_model: str, visual_model: str, visual_enabled: bool) -> dict:
    files = []
    for path in sorted(item for item in docs_dir.iterdir() if item.is_file()):
        files.append({
            "document_id": document_id(path),
            "filename": path.name,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "extension": path.suffix.lower(),
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "text_embedding_model": text_embedding_model,
        "visual_model": visual_model if visual_enabled else None,
        "visual_enabled": visual_enabled,
        "file_count": len(files),
        "files": files,
    }


def write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
