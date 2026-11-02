import re


NO_EVIDENCE_MESSAGE = (
    "I could not find enough indexed evidence to answer that reliably. "
    "Try a more specific question or ask the student community."
)


def verify_answer(answer: str, evidence: list[dict]) -> tuple[str, list[str]]:
    """Validate structural grounding without pretending to prove semantic entailment."""
    warnings: list[str] = []
    if not evidence:
        return NO_EVIDENCE_MESSAGE, ["no_evidence"]
    value = (answer or "").strip()
    if not value:
        return NO_EVIDENCE_MESSAGE, ["empty_provider_response"]

    cited = {int(number) for number in re.findall(r"\[E(\d+)\]", value)}
    invalid = sorted(number for number in cited if number < 1 or number > len(evidence))
    if invalid:
        warnings.append("invalid_citation_markers_removed")
        for number in invalid:
            value = value.replace(f"[E{number}]", "")
    if not cited:
        warnings.append("provider_omitted_inline_citations")
    return value, warnings
