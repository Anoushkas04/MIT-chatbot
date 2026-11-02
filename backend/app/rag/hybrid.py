from collections import defaultdict

from app.config import RAG_FINAL_K, RAG_TOP_K_TEXT, RAG_TOP_K_VISUAL, VISUAL_RAG_ENABLED
from app.llm import embed_query
from app.rag.keyword_store import get_keyword_store
from app.rag.store import get_store
from app.rag.visual_store import _metadata_tokens, get_visual_store


QUERY_ALIASES = {
    "artificial intelligence": "ai",
    "compiler design": "cd",
    "computer networks": "cn",
    "course plan": "cp",
    "database system": "dbs",
    "database systems": "dbs",
    "deep learning": "dl",
    "design and analysis of algorithms": "daa",
    "machine learning": "ml",
    "mechanical engineering": "me",
    "operating system": "os",
    "operating systems": "os",
}


def _expanded_query(query: str) -> str:
    normalized = " ".join(query.lower().split())
    aliases = {
        alias
        for phrase, alias in QUERY_ALIASES.items()
        if phrase in normalized
    }
    return f"{query} {' '.join(sorted(aliases))}".strip()


def _key(record: dict) -> str:
    return str(record.get("page_id") or record.get("id") or f"{record.get('source')}:{record.get('chunk_index')}")


def hybrid_search(query: str, final_k: int = RAG_FINAL_K) -> list[dict]:
    search_query = _expanded_query(query)
    result_lists: list[tuple[str, list[dict]]] = []
    try:
        dense = get_store().search(
            embed_query(search_query),
            raw_query=search_query,
            k=RAG_TOP_K_TEXT,
        )
        result_lists.append(("dense", dense))
    except Exception as exc:
        print(f"Dense retrieval unavailable: {exc}")

    try:
        result_lists.append(("bm25", get_keyword_store().search(search_query, k=RAG_TOP_K_TEXT)))
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
            source_name = str(record.get("source_file") or record.get("source", ""))
            metadata_matches = len(_metadata_tokens(query).intersection(_metadata_tokens(source_name)))
            weight = 1.25 if method == "colvision" else 1.0
            weight += min(metadata_matches, 5) * 0.25
            fused_scores[key] += weight / (60 + rank)
            methods[key].add(method)
            if key not in records or float(record.get("score", 0)) > float(records[key].get("score", 0)):
                records[key] = dict(record)

    if not fused_scores:
        return []
    maximum = max(fused_scores.values()) or 1.0
    query_metadata = _metadata_tokens(query)

    def source_matches(key: str) -> int:
        record = records[key]
        source_name = str(record.get("source_file") or record.get("source", ""))
        return len(query_metadata.intersection(_metadata_tokens(source_name)))

    # Promote one unambiguous source-title match. This handles corpus filenames
    # that use acronyms (ML, DBS, OS) and prevents a generic course plan that
    # appears in both dense and BM25 results from outranking the requested one.
    source_candidates: dict[str, tuple[int, float, str]] = {}
    for key in fused_scores:
        record = records[key]
        source_name = str(record.get("source_file") or record.get("source", ""))
        candidate = (source_matches(key), fused_scores[key], key)
        if source_name not in source_candidates or candidate[:2] > source_candidates[source_name][:2]:
            source_candidates[source_name] = candidate
    source_ranking = sorted(source_candidates.values(), reverse=True)
    promoted_metadata = None
    if source_ranking:
        top_matches, _, top_key = source_ranking[0]
        runner_up_matches = source_ranking[1][0] if len(source_ranking) > 1 else 0
        if top_matches >= 1 and top_matches > runner_up_matches:
            promoted_metadata = top_key

    visual_keys = [key for key in fused_scores if "colvision" in methods[key]]
    text_keys = [key for key in fused_scores if "colvision" not in methods[key]]
    promoted_visual = max(visual_keys, key=source_matches) if visual_keys else None
    best_text_metadata = max((source_matches(key) for key in text_keys), default=0)
    if promoted_visual and (
        source_matches(promoted_visual) < 2 or source_matches(promoted_visual) <= best_text_metadata
    ):
        promoted_visual = None

    ranked = sorted(
        fused_scores,
        key=lambda key: (
            key == promoted_metadata,
            key == promoted_visual,
            fused_scores[key],
        ),
        reverse=True,
    )
    output = []
    document_counts: dict[str, int] = defaultdict(int)
    promoted_documents = {
        str(records[key].get("document_id") or records[key].get("source"))
        for key in (promoted_metadata, promoted_visual)
        if key
    }
    for key in ranked:
        record = records[key]
        document = str(record.get("document_id") or record.get("source"))
        per_document_limit = 2 if document in promoted_documents else 1
        if document_counts[document] >= per_document_limit:
            continue
        document_counts[document] += 1
        record["score"] = (
            1.0
            if key in {promoted_metadata, promoted_visual}
            else fused_scores[key] / maximum
        )
        record["promoted_metadata"] = key == promoted_metadata
        record["promoted_visual"] = key == promoted_visual
        record["retrieval_method"] = "+".join(sorted(methods[key]))
        output.append(record)
        if len(output) >= final_k:
            break
    return output
