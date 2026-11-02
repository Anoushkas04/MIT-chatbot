import json
from pathlib import Path

from app.config import VISUAL_RAG_ENABLED
from app.rag.hybrid import hybrid_search


DEFAULT_FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "rag_queries.jsonl"


def run_evaluation(path: Path = DEFAULT_FIXTURE) -> dict:
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    evaluated = [case for case in cases if VISUAL_RAG_ENABLED or case["modality"] != "visual"]
    results = []
    for case in evaluated:
        hits = hybrid_search(case["question"])
        sources = [str(hit.get("source_file") or hit.get("source", "")) for hit in hits]
        passed = case["expected_source"] in sources
        results.append({"id": case["id"], "passed": passed, "sources": sources})
    passed = sum(result["passed"] for result in results)
    modality_metrics = {}
    for modality in sorted({case["modality"] for case in evaluated}):
        ids = {case["id"] for case in evaluated if case["modality"] == modality}
        subset = [result for result in results if result["id"] in ids]
        subset_passed = sum(result["passed"] for result in subset)
        modality_metrics[modality] = {
            "evaluated": len(subset),
            "passed": subset_passed,
            "recall_at_final_k": round(subset_passed / len(subset), 4) if subset else 0.0,
        }
    return {
        "total_fixtures": len(cases),
        "evaluated": len(results),
        "skipped_visual": len(cases) - len(results),
        "passed": passed,
        "recall_at_final_k": round(passed / len(results), 4) if results else 0.0,
        "by_modality": modality_metrics,
        "failures": [result for result in results if not result["passed"]],
    }


if __name__ == "__main__":
    print(json.dumps(run_evaluation(), indent=2))
