from collections import defaultdict
import re

from app.config import RAG_FINAL_K, RAG_TOP_K_TEXT, RAG_TOP_K_VISUAL, VISUAL_RAG_ENABLED
from app.llm import embed_query
from app.rag.keyword_store import get_keyword_store
from app.rag.metadata import normalize_department
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

MONTH_NUMBERS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}
GENERIC_SOURCE_TOKENS = {
    "btech", "course", "cp", "document", "pdf", "plan", "programme", "syllabus",
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
    return str(record.get("id") or record.get("page_id") or f"{record.get('source')}:{record.get('chunk_index')}")


def _source_title_match_score(query: str, source_name: str) -> int:
    query_tokens = _metadata_tokens(query)
    source_tokens = _metadata_tokens(source_name)
    distinctive_matches = (query_tokens - GENERIC_SOURCE_TOKENS).intersection(source_tokens)
    generic_matches = (query_tokens & GENERIC_SOURCE_TOKENS).intersection(source_tokens)
    return len(distinctive_matches) * 2 + min(len(generic_matches), 1)


def _context_score(
    record: dict,
    department: str | None,
    academic_year: str | None,
    semester: str | None,
) -> int:
    score = 0
    requested_code, requested_name = normalize_department(department)
    record_code, record_name = normalize_department(
        record.get("department_code") or record.get("department")
    )
    if department and (
        (requested_code and record_code == requested_code)
        or (requested_name and record_name and requested_name.lower() == record_name.lower())
    ):
        score += 3
    if academic_year and record.get("academic_year"):
        requested_year = academic_year.lower().replace("–", "-").replace(" ", "")
        record_year = str(record["academic_year"]).lower().replace("–", "-").replace(" ", "")
        if requested_year == record_year or requested_year in record_year or record_year in requested_year:
            score += 2
    if semester and record.get("semester"):
        if str(record["semester"]).lower() in semester.lower() or semester.lower() in str(record["semester"]).lower():
            score += 1
    return score


def _record_query_priority(record: dict, query: str) -> int:
    normalized = query.lower()
    score = 0
    requested_months = {
        month for name, month in MONTH_NUMBERS.items() if name in normalized
    }
    requested_years = {int(value) for value in re.findall(r"\b20\d{2}\b", normalized)}
    if record.get("calendar_month") and int(record["calendar_month"]) in requested_months:
        score += 2
    if record.get("calendar_year") and int(record["calendar_year"]) in requested_years:
        score += 3
    list_query = any(
        phrase in normalized
        for phrase in ("subjects", "course list", "courses offered", "curriculum", "first year")
    )
    if (
        list_query
        and record.get("page_number") == 1
        and record.get("document_type") in {"curriculum", "syllabus"}
    ):
        score += 3
    return score


def hybrid_search(
    query: str,
    final_k: int = RAG_FINAL_K,
    *,
    department: str | None = None,
    academic_year: str | None = None,
    semester: str | None = None,
) -> list[dict]:
    if final_k <= 0 or not query.strip():
        return []
    context = " ".join(value for value in (department, academic_year, semester) if value)
    search_query = _expanded_query(f"{query} {context}".strip())
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
            result_lists.append(("colvision", get_visual_store().search(search_query, k=RAG_TOP_K_VISUAL)))
        except Exception as exc:
            print(f"Visual retrieval unavailable: {exc}")

    fused_scores: dict[str, float] = defaultdict(float)
    records: dict[str, dict] = {}
    methods: dict[str, set[str]] = defaultdict(set)
    for method, values in result_lists:
        for rank, record in enumerate(values, start=1):
            key = _key(record)
            source_name = str(record.get("source_file") or record.get("source", ""))
            metadata_matches = _source_title_match_score(query, source_name)
            weight = 1.25 if method == "colvision" else 1.0
            weight += min(metadata_matches, 5) * 0.25
            weight += _context_score(record, department, academic_year, semester) * 0.35
            weight += _record_query_priority(record, query) * 0.4
            fused_scores[key] += weight / (60 + rank)
            methods[key].add(method)
            if key not in records or float(record.get("score", 0)) > float(records[key].get("score", 0)):
                records[key] = dict(record)

    if not fused_scores:
        return []
    maximum = max(fused_scores.values()) or 1.0
    def source_matches(key: str) -> int:
        record = records[key]
        source_name = str(record.get("source_file") or record.get("source", ""))
        return _source_title_match_score(search_query, source_name)

    # Promote one unambiguous source-title match. This handles corpus filenames
    # that use acronyms (ML, DBS, OS) and prevents a generic course plan that
    # appears in both dense and BM25 results from outranking the requested one.
    source_candidates: dict[str, tuple[int, int, float, str]] = {}
    for key in fused_scores:
        record = records[key]
        source_name = str(record.get("source_file") or record.get("source", ""))
        candidate = (
            source_matches(key),
            _record_query_priority(record, query),
            fused_scores[key],
            key,
        )
        if source_name not in source_candidates or candidate[:3] > source_candidates[source_name][:3]:
            source_candidates[source_name] = candidate
    source_ranking = sorted(source_candidates.values(), reverse=True)
    promoted_metadata = None
    if source_ranking:
        top_matches, _, _, top_key = source_ranking[0]
        runner_up_matches = source_ranking[1][0] if len(source_ranking) > 1 else 0
        if top_matches >= 3 and top_matches > runner_up_matches:
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
            bool(methods[key].intersection({"bm25", "dense"})),
            _record_query_priority(records[key], query),
            _context_score(records[key], department, academic_year, semester),
            fused_scores[key],
        ),
        reverse=True,
    )
    maximum_priority = max(
        (_record_query_priority(records[key], query) for key in fused_scores),
        default=0,
    )
    maximum_priority_context = max(
        (
            _context_score(records[key], department, academic_year, semester)
            for key in fused_scores
            if _record_query_priority(records[key], query) == maximum_priority
        ),
        default=0,
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
            or (
                maximum_priority > 0
                and _record_query_priority(record, query) == maximum_priority
                and _context_score(record, department, academic_year, semester)
                == maximum_priority_context
            )
            else fused_scores[key] / maximum
        )
        record["promoted_metadata"] = key == promoted_metadata
        record["promoted_visual"] = key == promoted_visual
        record["retrieval_method"] = "+".join(sorted(methods[key]))
        output.append(record)
        if len(output) >= final_k:
            break
    return output
