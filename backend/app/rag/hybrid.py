from collections import defaultdict

from app.config import RAG_FINAL_K, RAG_TOP_K_TEXT, RAG_TOP_K_VISUAL, VISUAL_RAG_ENABLED
from app.llm import embed_query
from app.rag.keyword_store import get_keyword_store
from app.rag.store import get_store
from app.rag.visual_store import get_visual_store


def _key(record: dict) -> str:
    return str(record.get("page_id") or record.get("id") or f"{record.get('source')}:{record.get('chunk_index')}")


def hybrid_search(query: str, final_k: int = RAG_FINAL_K) -> list[dict]:
    result_lists: list[tuple[str, list[dict]]] = []
    try:
        dense = get_store().search(embed_query(query), raw_query=query, k=RAG_TOP_K_TEXT)
        result_lists.append(("dense", dense))
    except Exception as exc:
        print(f"Dense retrieval unavailable: {exc}")

    try:
        result_lists.append(("bm25", get_keyword_store().search(query, k=RAG_TOP_K_TEXT)))
    except Exception as exc:
        print(f"BM25 retrieval unavailable: {exc}")

    if VISUAL_RAG_ENABLED:
        try:
            result_lists.append(("colvision", get_visual_store().search(query, k=RAG_TOP_K_VISUAL)))
        except Exception as exc:
            print(f"Visual retrieval unavailable: {exc}")

    fused_scores: dict[str, float] = defaultdict(float)
    records: dict[str, dict] = {}
    methods: dict[str, set[str]] = defaultdict(set)
    for method, values in result_lists:
        for rank, record in enumerate(values, start=1):
            key = _key(record)
            fused_scores[key] += 1.0 / (60 + rank)
            methods[key].add(method)
            if key not in records or float(record.get("score", 0)) > float(records[key].get("score", 0)):
                records[key] = dict(record)

    if not fused_scores:
        return []
    maximum = max(fused_scores.values()) or 1.0
    ranked = sorted(fused_scores, key=fused_scores.get, reverse=True)
    output = []
    document_counts: dict[str, int] = defaultdict(int)
    for key in ranked:
        record = records[key]
        document = str(record.get("document_id") or record.get("source"))
        if document_counts[document] >= 2:
            continue
        document_counts[document] += 1
        record["score"] = fused_scores[key] / maximum
        record["retrieval_method"] = "+".join(sorted(methods[key]))
        output.append(record)
        if len(output) >= final_k:
            break
    return output
