import app.providers.registry as registry
from app.providers.base import GenerationRequest, GenerationResult


class Failing:
    name = "gemini"
    def generate(self, request): raise RuntimeError("429 quota")
    def complete(self, system, prompt): raise RuntimeError("429 quota")


class Working:
    name = "openai"
    def generate(self, request): return GenerationResult("From the backup model [E1].", self.name, "m")
    def complete(self, system, prompt): return "When is REVELS?"


REQUEST = GenerationRequest(question="q", system_prompt="s", evidence=[{"text": "REVELS is on 17 Feb 2027.", "source": "cal"}])


def test_a_failing_model_hands_over_to_the_next_configured_one(monkeypatch):
    monkeypatch.setattr(registry, "get_provider", lambda: Failing())
    monkeypatch.setattr(registry, "fallback_names", lambda: ["openai"])
    monkeypatch.setattr(registry, "_build", lambda name: Working())
    assert registry.generate_answer(REQUEST).provider == "openai"
    assert registry.complete_text("s", "रेवल्स कब है?") == "When is REVELS?"


def test_with_no_other_model_it_falls_back_to_local(monkeypatch):
    monkeypatch.setattr(registry, "get_provider", lambda: Failing())
    monkeypatch.setattr(registry, "fallback_names", lambda: [])
    assert registry.generate_answer(REQUEST).provider == "local"
    assert registry.complete_text("s", "x") is None
