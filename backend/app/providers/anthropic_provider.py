import anthropic

from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, LLM_TIMEOUT_SECONDS
from app.providers.base import GenerationRequest, GenerationResult, Provider, evidence_text, image_payloads


class AnthropicProvider(Provider):
    name = "anthropic"
    model = ANTHROPIC_MODEL

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=ANTHROPIC_API_KEY,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=1,
        )

    def generate(self, request: GenerationRequest) -> GenerationResult:
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": mime, "data": data}}
            for mime, data in image_payloads(request.evidence)
        ]
        content.append({"type": "text", "text": evidence_text(request)})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1200,
            system=request.system_prompt,
            messages=[{"role": "user", "content": content}],
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        return GenerationResult(text=text.strip(), provider=self.name, model=self.model)

    def complete(self, system: str, prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if getattr(block, "type", None) == "text").strip()
