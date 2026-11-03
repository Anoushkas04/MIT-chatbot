"""Offline L2 acceptance evaluation for the selected MIT chatbot corpus.

The evaluator deliberately uses the production hybrid retriever and the local
evidence-only answer provider. It never calls Gemini, OpenAI, or Anthropic.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from app.answer_verifier import NO_EVIDENCE_MESSAGE, verify_answer
from app.providers.base import GenerationRequest
from app.providers.local_provider import LocalProvider
from app.rag.hybrid import hybrid_search


DEFAULT_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "l2_chatbot_queries.jsonl"
)

SELECTED_CORPUS = {
    "MIT - UG - Hand Book-- 2024 - Revised.pdf": {
        "MIT - UG - Hand Book-- 2024 - Revised.pdf"
    },
    "Regulations 2026 B.Tech.pdf": {"Regulations 2026 B.Tech.pdf"},
    "Academic Calendar 26-27 (1).pdf": {"Academic Calendar 26-27 (1).pdf"},
    "AttachmentMIT_INR_compressed..pdf": {"AttachmentMIT_INR_compressed..pdf"},
    "BTech_Common_Counseling_2026_Cutoff_Rank_Round_2.pdf": {
        "BTech_Common_Counseling_2026_Cutoff_Rank_Round_2.pdf"
    },
    "PLACEMENT GUIDELINES 13 JULY 2024 FINAL_250905_124353.pdf": {
        "PLACEMENT GUIDELINES 13 JULY 2024 FINAL_250905_124353.pdf"
    },
    "BTech_CSE_Syllabus_2026.pdf": {"BTech_CSE_Syllabus_2026.pdf"},
    "First year Core 2026 B.Tech.pdf": {"First year Core 2026 B.Tech.pdf"},
    "First year CS 2026 B.Tech.pdf": {"First year CS 2026 B.Tech.pdf"},
    "clubs.pdf": {"clubs.pdf"},
    "manipal_sce_faculty_cabins.csv": {
        "manipal_sce_faculty_cabins.csv",
        "School of Computer Engineering faculty list, July 2026",
    },
    "mit_manipal_faculty.csv": {"mit_manipal_faculty.csv"},
}


def load_cases(path: Path = DEFAULT_FIXTURE) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _normalized(value: object) -> str:
    normalized = re.sub(r"\s+", " ", str(value)).strip().casefold()
    return re.sub(r"(?<=\d)\s+%", "%", normalized)


def _source_name(hit: dict) -> str:
    return str(hit.get("source_file") or hit.get("source") or "")


def _matching_hits(case: dict, hits: list[dict]) -> list[dict]:
    aliases = SELECTED_CORPUS[case["source_file"]]
    return [hit for hit in hits if _source_name(hit) in aliases]


def evaluate_case(case: dict) -> dict:
    hits = hybrid_search(case["question"])
    matching = _matching_hits(case, hits)
    evidence_text = _normalized(" ".join(hit.get("text", "") for hit in matching))
    expected_terms = case.get("expected_terms", [])
    evidence_supported = bool(matching) and any(
        _normalized(term) in evidence_text for term in expected_terms
    )

    answer = ""
    warnings: list[str] = []
    answer_grounded = False
    if matching:
        generation = LocalProvider().generate(
            GenerationRequest(
                question=case["question"],
                system_prompt="Answer only from the supplied MIT corpus evidence.",
                evidence=matching,
            )
        )
        answer, warnings = verify_answer(generation.text, matching)
        valid_marker = re.search(rf"\[E(?:{'|'.join(str(index) for index in range(1, len(matching) + 1))})\]", answer)
        answer_grounded = answer != NO_EVIDENCE_MESSAGE and bool(valid_marker)

    return {
        "id": case["id"],
        "source_file": case["source_file"],
        "category": case["category"],
        "retrieval_passed": bool(matching),
        "evidence_supported": evidence_supported,
        "answer_grounded": answer_grounded,
        "passed": bool(matching) and evidence_supported and answer_grounded,
        "retrieved_sources": [_source_name(hit) for hit in hits],
        "answer": answer,
        "warnings": warnings,
    }


def run_evaluation(path: Path = DEFAULT_FIXTURE) -> dict:
    cases = load_cases(path)
    results = [evaluate_case(case) for case in cases]
    passed = sum(result["passed"] for result in results)
    source_counts = Counter(case["source_file"] for case in cases)
    category_counts = Counter(case["category"] for case in cases)

    return {
        "level": "L2",
        "network_llm_calls": 0,
        "selected_sources": len(SELECTED_CORPUS),
        "total_cases": len(cases),
        "passed": passed,
        "pass_rate": round(passed / len(results), 4) if results else 0.0,
        "retrieval_passed": sum(result["retrieval_passed"] for result in results),
        "evidence_supported": sum(result["evidence_supported"] for result in results),
        "answers_grounded": sum(result["answer_grounded"] for result in results),
        "cases_by_source": dict(sorted(source_counts.items())),
        "cases_by_category": dict(sorted(category_counts.items())),
        "failures": [result for result in results if not result["passed"]],
    }


if __name__ == "__main__":
    report = run_evaluation()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if not report["failures"] else 1)
