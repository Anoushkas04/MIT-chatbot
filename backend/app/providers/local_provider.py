import re

from app.answer_verifier import NO_EVIDENCE_MESSAGE
from app.providers.base import GenerationRequest, GenerationResult, Provider


class LocalProvider(Provider):
    name = "local"
    model = "extractive-evidence-v1"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        terms = {
            word for word in re.findall(r"[a-z0-9]+", request.question.lower())
            if len(word) > 2 and word not in {"what", "where", "when", "which", "with", "the", "for"}
        }
        candidates = []
        for index, item in enumerate(request.evidence, start=1):
            value = " ".join(str(item.get("text", "")).split())
            if not value:
                continue
            score = sum(term in value.lower() for term in terms)
            candidates.append((score, index, value))
        candidates.sort(reverse=True)
        selected = [candidate for candidate in candidates if candidate[0] > 0][:2] or candidates[:1]
        if not selected:
            text = NO_EVIDENCE_MESSAGE
        else:
            excerpts = []
            for _, index, value in selected:
                excerpt = value[:450].rsplit(" ", 1)[0] if len(value) > 450 else value
                excerpts.append(f"{excerpt} [E{index}]")
            text = "Based on the retrieved campus sources: " + " ".join(excerpts)
        return GenerationResult(text=text, provider=self.name, model=self.model)
