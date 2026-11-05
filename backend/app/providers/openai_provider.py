from openai import OpenAI

from app.config import LLM_TIMEOUT_SECONDS, OPENAI_API_KEY, OPENAI_MODEL
from app.providers.base import GenerationRequest, GenerationResult, Provider, evidence_text, image_payloads


class OpenAIProvider(Provider):
    name = "openai"
    model = OPENAI_MODEL

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY, timeout=LLM_TIMEOUT_SECONDS, max_retries=1)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        content = [{"type": "input_text", "text": evidence_text(request)}]
        content.extend({"type": "input_image", "image_url": f"data:{mime};base64,{data}"} for mime, data in image_payloads(request.evidence))
        response = self.client.responses.create(
            model=self.model,
            instructions=request.system_prompt,
            input=[{"role": "user", "content": content}],
        )
        return GenerationResult(text=response.output_text.strip(), provider=self.name, model=self.model)

    def complete(self, system: str, prompt: str) -> str:
        response = self.client.responses.create(model=self.model, instructions=system, input=prompt)
        return response.output_text.strip()
