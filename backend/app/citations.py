"""Choosing which retrieved passages become citations.

Retrieval returns several candidate passages, but only the ones the answer actually relies
on are sources. An [E<n>] marker is kept only if passage n supports the claim it's attached
to (most of the claim's content words appear in it) and is relevant to the question.
Unsupported markers are removed, the kept ones are renumbered 1, 2, 3 in reading order,
and only those passages are returned. A closing "Source: ... [E1]" line cites the whole
answer, so it's checked against the answer's text. An answer with no supported marker gets
no citations.
"""
import re

from app.rag.rerank import _alternatives, query_terms, relevance
from app.rag.text_norm import index_tokens

MARKER = re.compile(r"\[E(\d+)\]")
CLAIM_SUPPORT = 0.5  # share of a claim's content words found in the cited passage
QUESTION_RELEVANCE = 0.2  # a cited passage must also cover this much of the question
STRUCTURED = {"structured_calendar", "structured_clubs", "structured_faculty_directory"}
NOISE = {"mit", "manipal", "mahe", "official", "source", "document", "page"}


def _words(text: str) -> set[str]:
    return {t for t in index_tokens(text) if t not in NOISE}


def supports(claim: str, passage: dict) -> bool:
    """Does the passage contain most of what the claim says?"""
    claim_words = _words(MARKER.sub(" ", claim).replace("…", " "))
    if not claim_words:
        return False
    have = _words(" ".join(str(passage.get(k, "")) for k in ("source", "source_file", "text")))
    alts = _alternatives()
    covered = sum(1 for w in claim_words if w in have or alts.get(w, set()) & have)
    return covered / len(claim_words) >= CLAIM_SUPPORT and (covered >= 2 or len(claim_words) == 1)


def _relevant(question: str, passage: dict) -> bool:
    if passage.get("retrieval_method") in STRUCTURED or str(passage.get("document_type")) == "faculty_directory":
        return True  # exact lookups for this question
    terms = query_terms(question)
    return not terms or relevance(terms, passage) >= QUESTION_RELEVANCE


def select_citations(answer: str, evidence: list[dict], question: str) -> tuple[str, list[tuple[int, dict]]]:
    """The answer with only supported, renumbered markers, and the (new index, passage) cited."""
    if not answer or not evidence:
        return MARKER.sub("", answer or "").strip(), []
    body = "\n".join(l for l in answer.splitlines() if not l.strip().lower().startswith("source:"))
    order: list[int] = []

    def keep(claim: str, n: int) -> bool:
        if not 1 <= n <= len(evidence):
            return False
        passage = evidence[n - 1]
        if not (supports(claim, passage) and _relevant(question, passage)):
            return False
        if n not in order:
            order.append(n)
        return True

    lines = []
    for line in answer.splitlines():
        # A closing "Source: ... [E1]" line cites the whole answer
        whole_answer = line.strip().lower().startswith("source:")
        out, claim = [], ""
        for part in re.split(r"(\[E\d+\])", line):
            marker = MARKER.fullmatch(part)
            if marker:
                if keep(body if whole_answer else claim, int(marker.group(1))):
                    out.append(f"[K{marker.group(1)}]")
            else:
                if part.strip():
                    claim = part  # the text this and following markers cite
                out.append(part)
        rebuilt = re.sub(r"[ \t]{2,}", " ", "".join(out)).replace(" .", ".").rstrip()
        if whole_answer and "[K" not in rebuilt:
            continue  # a source line with nothing left to cite says nothing
        lines.append(rebuilt)
    renumber = {old: new for new, old in enumerate(order, start=1)}
    text = re.sub(r"\[K(\d+)\]", lambda m: f"[E{renumber[int(m.group(1))]}]", "\n".join(lines))
    return text.strip(), [(renumber[old], evidence[old - 1]) for old in order]
