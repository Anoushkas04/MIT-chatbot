from functools import lru_cache

from app.config import ANTHROPIC_API_KEY, GEMINI_API_KEY, LLM_PROVIDER, OPENAI_API_KEY
from app.providers.base import GenerationRequest, GenerationResult, Provider


def _available() -> dict[str, bool]:
    return {
        "openai": bool(OPENAI_API_KEY.strip()),
        "anthropic": bool(ANTHROPIC_API_KEY.strip()),
        "gemini": bool(GEMINI_API_KEY.strip()),
        "local": True,
    }


def selected_provider_name() -> str:
    available = _available()
    if LLM_PROVIDER != "auto":
        if LLM_PROVIDER not in available:
            raise RuntimeError(f"Unsupported LLM_PROVIDER '{LLM_PROVIDER}'.")
        if not available[LLM_PROVIDER]:
            raise RuntimeError(f"LLM_PROVIDER '{LLM_PROVIDER}' is selected but its API key is missing.")
        return LLM_PROVIDER
    return next(name for name in ("openai", "anthropic", "gemini", "local") if available[name])


@lru_cache
def get_provider() -> Provider:
    name = selected_provider_name()
    if name == "openai":
        from app.providers.openai_provider import OpenAIProvider
        return OpenAIProvider()
    if name == "anthropic":
        from app.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    if name == "gemini":
        from app.providers.gemini_provider import GeminiProvider
        return GeminiProvider()
    from app.providers.local_provider import LocalProvider
    return LocalProvider()


def generate_answer(request: GenerationRequest) -> GenerationResult:
    provider = get_provider()
    try:
        result = provider.generate(request)
        if not result.text:
            raise RuntimeError("The selected provider returned an empty answer.")
        return result
    except Exception as exc:
        if provider.name == "local":
            raise
        print(f"{provider.name} generation failed; using evidence-only fallback: {exc}")
        from app.providers.local_provider import LocalProvider
        return LocalProvider().generate(request)


def get_provider_status() -> dict:
    try:
        selected = selected_provider_name()
        error = None
    except RuntimeError as exc:
        selected = None
        error = str(exc)
    return {"configured": _available(), "selected": selected, "error": error}
