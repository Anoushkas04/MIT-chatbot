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
def _build(name: str) -> Provider:
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


def get_provider() -> Provider:
    return _build(selected_provider_name())


def fallback_names() -> list[str]:
    """Other models with keys, tried in order when the selected one fails (quota, outage)."""
    available = _available()
    first = selected_provider_name()
    return [n for n in ("gemini", "openai", "anthropic") if available[n] and n != first]


def _chain() -> list[Provider]:
    # The selected provider first, then any other configured model; local mode is the last resort
    return [get_provider(), *(_build(n) for n in fallback_names())]


def generate_answer(request: GenerationRequest) -> GenerationResult:
    for provider in _chain():
        if provider.name == "local":
            break
        try:
            result = provider.generate(request)
            if not result.text:
                raise RuntimeError("returned an empty answer")
            return result
        except Exception as exc:
            print(f"{provider.name} generation failed; trying the next model: {exc}")
    from app.providers.local_provider import LocalProvider
    return LocalProvider().generate(request)


def complete_text(system: str, prompt: str) -> str | None:
    """A plain completion from the first model that answers, or None in local mode or if all fail."""
    for provider in _chain():
        if provider.name == "local":
            return None
        try:
            text = provider.complete(system, prompt)
            if text:
                return text
        except Exception as exc:
            print(f"{provider.name} completion failed; trying the next model: {exc}")
    return None


def get_provider_status() -> dict:
    try:
        selected = selected_provider_name()
        error = None
    except RuntimeError as exc:
        selected = None
        error = str(exc)
    return {
        "configured": _available(),
        "selected": selected,
        "fallbacks": (fallback_names() if selected else []) + ["local"],
        "error": error,
    }
