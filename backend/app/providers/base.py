import base64
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path

from app.config import DATA_DIR


@dataclass
class GenerationRequest:
    question: str
    system_prompt: str
    evidence: list[dict]
    history: list[dict] = field(default_factory=list)


@dataclass
class GenerationResult:
    text: str
    provider: str
    model: str


class Provider:
    name = "base"
    model = "unknown"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        raise NotImplementedError


def evidence_text(request: GenerationRequest) -> str:
    blocks = []
    for index, item in enumerate(request.evidence, start=1):
        page = f", page {item['page_number']}" if item.get("page_number") else ""
        text = item.get("text", "").strip() or "[Visual page; inspect the attached image.]"
        blocks.append(f"[E{index}: {item.get('source', 'Source')}{page}]\n{text}")
    history = "\n".join(f"{turn.get('role')}: {turn.get('text')}" for turn in request.history[-6:])
    return (
        f"Conversation history:\n{history or '[none]'}\n\n"
        f"Retrieved evidence:\n{'\n\n'.join(blocks)}\n\n"
        f"Question: {request.question}\n\n"
        "Answer only from the retrieved evidence. Cite evidence inline as [E1], [E2], etc. "
        "If the evidence does not answer the question, say that clearly and do not guess."
    )


def image_payloads(evidence: list[dict]) -> list[tuple[str, str]]:
    payloads = []
    for item in evidence:
        relative = item.get("image_path")
        if not relative:
            continue
        path = DATA_DIR / relative
        if not path.is_file():
            continue
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        payloads.append((mime, base64.b64encode(path.read_bytes()).decode("ascii")))
    return payloads
