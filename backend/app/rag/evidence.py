from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class Evidence:
    id: str
    source: str
    text: str
    score: float
    retrieval_method: str
    document_id: Optional[str] = None
    page_number: Optional[int] = None
    image_path: Optional[str] = None
    source_type: str = "official"

    def to_dict(self) -> dict:
        return asdict(self)


def evidence_from_record(record: dict, score: float, method: str) -> Evidence:
    return Evidence(
        id=str(record.get("id") or record.get("page_id") or record.get("source", "source")),
        source=str(record.get("source", "Institutional Knowledge Base")),
        text=str(record.get("text", "")),
        score=float(score),
        retrieval_method=method,
        document_id=record.get("document_id"),
        page_number=record.get("page_number"),
        image_path=record.get("image_path"),
        source_type=str(record.get("source_type", "official")),
    )
