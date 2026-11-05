import json
import math
from pathlib import Path

from app.config import VISUAL_RAG_ENABLED
from app.rag.hybrid import hybrid_search


DEFAULT_FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "rag_queries.jsonl"


def _rank(hits: list[dict], expected: str) -> int | None:
    """1-based position of the expected document among the distinct documents retrieved."""
    seen: list[str] = []
    for hit in hits:
        source = str(hit.get("source_file") or hit.get("source", ""))
        if source not in seen:
            seen.append(source)
    return seen.index(expected) + 1 if expected in seen else None


def _ranking(ranks: list) -> dict:
    n = len(ranks)
    return {
        "recall_at_5": round(sum(1 for r in ranks if r) / n, 4) if n else 0.0,
        "mrr": round(sum(1 / r for r in ranks if r) / n, 4) if n else 0.0,
        # one relevant document per question, so the ideal DCG is 1
        "ndcg_at_5": round(sum(1 / math.log2(r + 1) for r in ranks if r) / n, 4) if n else 0.0,
    }


def run_evaluation(path: Path = DEFAULT_FIXTURE) -> dict:
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    evaluated = [case for case in cases if VISUAL_RAG_ENABLED or case["modality"] != "visual"]
    results = []
    for case in evaluated:
        hits = hybrid_search(case["question"], final_k=5)
        sources = [str(hit.get("source_file") or hit.get("source", "")) for hit in hits]
        rank = _rank(hits, case["expected_source"])
        # "passed" keeps its original meaning: the expected document is in the final 4 sent to the answer
        results.append({"id": case["id"], "passed": rank is not None and rank <= 4, "rank": rank, "sources": sources})
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
            **_ranking([result["rank"] for result in subset]),
        }
    return {
        "total_fixtures": len(cases),
        "evaluated": len(results),
        "skipped_visual": len(cases) - len(results),
        "passed": passed,
        "recall_at_final_k": round(passed / len(results), 4) if results else 0.0,
        **_ranking([result["rank"] for result in results]),
        "by_modality": modality_metrics,
        "failures": [result for result in results if not result["passed"]],
    }


if __name__ == "__main__":
    print(json.dumps(run_evaluation(), indent=2))
