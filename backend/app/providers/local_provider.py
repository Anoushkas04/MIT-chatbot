import re

from app.answer_verifier import NO_EVIDENCE_MESSAGE
from app.providers.base import GenerationRequest, GenerationResult, Provider


class LocalProvider(Provider):
    name = "local"
    model = "extractive-evidence-v1"

    @staticmethod
    def _sentences(value: str) -> list[str]:
        clean = " ".join(value.split())
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", clean)
        return [sentence.strip() for sentence in sentences if len(sentence.strip()) >= 20]

    @staticmethod
    def _structured_answer(evidence: list[dict]) -> str | None:
        """Calendar entries and club records are already the answer: list them as-is."""
        calendar = [(i, e) for i, e in enumerate(evidence, start=1) if e.get("retrieval_method") == "structured_calendar"]
        if calendar:
            index, item = calendar[0]
            lines = [line for line in str(item.get("text", "")).splitlines() if line.startswith("- ")]
            return "From the Academic Calendar 2026-27:\n" + "\n".join(lines) + f" [E{index}]"
        clubs = [(i, e) for i, e in enumerate(evidence, start=1) if e.get("retrieval_method") == "structured_clubs"]
        if not clubs:
            return None
        if len(clubs) == 1 and clubs[0][1].get("kind") != "club":  # the full list
            index, item = clubs[0]
            return str(item.get("text", "")) + f" [E{index}]"
        lines = []
        for index, item in clubs:
            text = str(item.get("text", ""))
            head, _, rest = text.partition(". ")
            summary = LocalProvider._sentences(rest)[:1]
            lines.append(f"- {head}. {summary[0] if summary else ''} [E{index}]".rstrip())
        return "These official MIT clubs match:\n" + "\n".join(lines)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if request.evidence and request.evidence[0].get("image_path") and not request.evidence[0].get("text"):
            return GenerationResult(
                text=(
                    "I found a relevant scanned page [E1], but local extractive mode cannot interpret "
                    "the page image. Configure an OpenAI, Anthropic, or Gemini API key to answer from it."
                ),
                provider=self.name,
                model=self.model,
            )
        structured = self._structured_answer(request.evidence)
        if structured:
            return GenerationResult(text=structured, provider=self.name, model=self.model)
        terms = {
            word for word in re.findall(r"[a-z0-9]+", request.question.lower())
            if len(word) > 2 and word not in {"what", "where", "when", "which", "with", "the", "for"}
        }
        candidates = []
        for index, item in enumerate(request.evidence, start=1):
            for sentence in self._sentences(str(item.get("text", ""))):
                normalized = sentence.lower()
                score = sum(term in normalized for term in terms)
                if re.search(r"\b\d+(?:\.\d+)?\s*%|\b\d{4}\b", sentence):
                    score += 1
                candidates.append((score, index, sentence))
        candidates.sort(reverse=True)
        selected = []
        seen = set()
        for candidate in [item for item in candidates if item[0] > 0] or candidates[:1]:
            fingerprint = candidate[2].lower()
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            selected.append(candidate)
            if len(selected) == 2:
                break
        if not selected:
            visual = next((index for index, item in enumerate(request.evidence, start=1) if item.get("image_path")), None)
            if visual:
                text = (
                    f"I found a relevant scanned page [E{visual}], but local extractive mode cannot interpret "
                    "the page image. Configure an OpenAI, Anthropic, or Gemini API key to answer from it."
                )
            else:
                text = NO_EVIDENCE_MESSAGE
        else:
            excerpts = []
            for _, index, value in selected:
                excerpt = value[:280].rsplit(" ", 1)[0] + "…" if len(value) > 280 else value
                excerpts.append(f"{excerpt} [E{index}]")
            text = " ".join(excerpts)
        return GenerationResult(text=text, provider=self.name, model=self.model)
