from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.providers.base import GenerationRequest, GenerationResult, Provider, evidence_text, image_payloads


class GeminiProvider(Provider):
    name = "gemini"
    model = GEMINI_MODEL

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        contents = [evidence_text(request)]
        contents.extend(types.Part.from_bytes(data=__import__("base64").b64decode(data), mime_type=mime) for mime, data in image_payloads(request.evidence))
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=request.system_prompt),
        )
        return GenerationResult(text=(response.text or "").strip(), provider=self.name, model=self.model)
