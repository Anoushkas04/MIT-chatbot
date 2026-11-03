import json
import os
import re
from functools import lru_cache
from pathlib import Path

from app.config import (
    COLVISION_DEVICE,
    COLVISION_LOCAL_FILES_ONLY,
    COLVISION_MODEL,
    DATA_DIR,
    VISUAL_RAG_SCOPE,
)


VISUAL_EMBEDDINGS_PATH = DATA_DIR / "visual_embeddings.pt"
VISUAL_MANIFEST_PATH = DATA_DIR / "visual_manifest.json"
VISUAL_MODEL_READY_PATH = DATA_DIR / "visual_model_ready.json"


def _device() -> str:
    import torch
    if COLVISION_DEVICE != "auto":
        if COLVISION_DEVICE.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("COLVISION_DEVICE requests CUDA, but this PyTorch build cannot access CUDA.")
        return COLVISION_DEVICE
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache
def get_visual_model():
    import torch
    from sentence_transformers import MultiVectorEncoder
    device = _device()
    model_kwargs = {"torch_dtype": torch.float16} if device.startswith("cuda") else {}
    return MultiVectorEncoder(
        COLVISION_MODEL,
        device=device,
        token=os.environ.get("HF_TOKEN") or None,
        local_files_only=COLVISION_LOCAL_FILES_ONLY,
        model_kwargs=model_kwargs,
    )


def build_visual_index(pages: list[dict], image_root: Path, progress_callback=None) -> dict:
    import torch
    progress = progress_callback or (lambda percent, message: None)
    candidates = [page for page in pages if page.get("image_path")]
    if not candidates:
        raise RuntimeError("No rendered page images are available for visual indexing.")
    model = get_visual_model()
    embeddings = []
    # Batch size one is deliberate for 4 GB laptop GPUs.
    batch_size = 1
    for start in range(0, len(candidates), batch_size):
        batch = candidates[start:start + batch_size]
        paths = [str(image_root / Path(page["image_path"]).name) for page in batch]
        try:
            encoded = model.encode_document(paths, batch_size=batch_size, convert_to_numpy=False, show_progress_bar=False)
        except torch.OutOfMemoryError as exc:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise RuntimeError(
                "The visual encoder exhausted GPU memory. Close other GPU applications or set COLVISION_DEVICE=cpu."
            ) from exc
        if isinstance(encoded, torch.Tensor):
            encoded = list(torch.unbind(encoded))
        embeddings.extend(item.detach().cpu().to(torch.float16) for item in encoded)
        progress(int((start + len(batch)) / len(candidates) * 100), f"Visual pages {start + len(batch)}/{len(candidates)}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    torch.save({"embeddings": embeddings, "pages": candidates}, VISUAL_EMBEDDINGS_PATH)
    VISUAL_MANIFEST_PATH.write_text(json.dumps({
        "model": COLVISION_MODEL,
        "device": _device(),
        "page_count": len(candidates),
        "scope": VISUAL_RAG_SCOPE,
        "storage_dtype": "float16",
    }, indent=2), encoding="utf-8")
    clear_visual_cache()
    return {"page_count": len(candidates), "model": COLVISION_MODEL, "device": _device(), "scope": VISUAL_RAG_SCOPE}


class VisualStore:
    def __init__(self):
        import torch
        if not VISUAL_EMBEDDINGS_PATH.exists() or not VISUAL_MANIFEST_PATH.exists():
            raise FileNotFoundError("No visual index found. Run multimodal ingestion first.")
        bundle = torch.load(VISUAL_EMBEDDINGS_PATH, map_location="cpu", weights_only=False)
        self.embeddings = bundle["embeddings"]
        self.pages = bundle["pages"]
        self.manifest = json.loads(VISUAL_MANIFEST_PATH.read_text(encoding="utf-8"))
        if len(self.embeddings) != len(self.pages):
            raise ValueError("Visual page metadata and embeddings have different lengths.")

    def search(self, query: str, k: int = 8) -> list[dict]:
        import torch
        model = get_visual_model()
        query_embeddings = model.encode_query([query], batch_size=1, convert_to_numpy=False, show_progress_bar=False)
        query_device = query_embeddings.device if isinstance(query_embeddings, torch.Tensor) else query_embeddings[0].device
        document_embeddings = [embedding.to(query_device) for embedding in self.embeddings]
        scores = model.similarity(query_embeddings, document_embeddings).detach().cpu().reshape(-1)
        query_tokens = _metadata_tokens(query)
        adjusted = []
        metadata_matches = []
        for index, page in enumerate(self.pages):
            matches = len(query_tokens.intersection(_metadata_tokens(str(page.get("source", "")))))
            metadata_matches.append(matches)
            adjusted.append(float(scores[index]) + min(matches, 5) * 1.5)
        promoted_source = _promoted_metadata_source(query, self.pages)
        indices = sorted(
            range(len(adjusted)),
            key=lambda index: (
                str(self.pages[index].get("source", "")) == promoted_source,
                adjusted[index],
            ),
            reverse=True,
        )[:k]
        return [
            {
                **self.pages[int(index)],
                "score": adjusted[int(index)],
                "visual_score": float(scores[index]),
                "metadata_matches": metadata_matches[int(index)],
                "retrieval_method": "colvision",
            }
            for index in indices
        ]


def _metadata_tokens(value: str) -> set[str]:
    # Split CamelCase filenames such as AttachmentMIT before lowercasing.
    expanded = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    tokens = {token for token in re.findall(r"[a-z0-9]+", expanded.lower()) if len(token) > 1}
    for token in tuple(tokens):
        if len(token) == 4 and token.startswith("20"):
            tokens.add(token[2:])
    if "computer" in tokens and "science" in tokens:
        tokens.add("cs")
    if "cs" in tokens:
        tokens.update({"computer", "science"})
    phrase_aliases = {
        frozenset({"artificial", "intelligence"}): "ai",
        frozenset({"compiler", "design"}): "cd",
        frozenset({"computer", "networks"}): "cn",
        frozenset({"course", "plan"}): "cp",
        frozenset({"database", "system"}): "dbs",
        frozenset({"database", "systems"}): "dbs",
        frozenset({"deep", "learning"}): "dl",
        frozenset({"machine", "learning"}): "ml",
        frozenset({"mechanical", "engineering"}): "me",
        frozenset({"operating", "system"}): "os",
        frozenset({"operating", "systems"}): "os",
    }
    for phrase, alias in phrase_aliases.items():
        if phrase.issubset(tokens):
            tokens.add(alias)
    return tokens


def _promoted_metadata_source(query: str, pages: list[dict]) -> str | None:
    """Promote one unambiguous filename match above noisy visual similarity."""
    query_tokens = _metadata_tokens(query)
    source_matches: dict[str, int] = {}
    for page in pages:
        source = str(page.get("source", ""))
        source_matches[source] = max(
            source_matches.get(source, 0),
            len(query_tokens.intersection(_metadata_tokens(source))),
        )
    ranking = sorted(
        ((matches, source) for source, matches in source_matches.items()),
        reverse=True,
    )
    if not ranking:
        return None
    top_matches, top_source = ranking[0]
    runner_up_matches = ranking[1][0] if len(ranking) > 1 else 0
    return top_source if top_matches >= 3 and top_matches > runner_up_matches else None


@lru_cache
def get_visual_store() -> VisualStore:
    return VisualStore()


def clear_visual_cache() -> None:
    get_visual_store.cache_clear()


def get_visual_status() -> dict:
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        hardware = {
            "torch_version": torch.__version__,
            "cuda_available": cuda_available,
            "cuda_runtime": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0) if cuda_available else None,
        }
    except ImportError:
        hardware = {
            "torch_version": None,
            "cuda_available": False,
            "cuda_runtime": None,
            "gpu": None,
        }
    try:
        store = get_visual_store()
        return {
            "ready": True,
            "page_count": len(store.pages),
            "model": store.manifest.get("model"),
            "device": _device(),
            "scope": store.manifest.get("scope"),
            "model_prefetched": VISUAL_MODEL_READY_PATH.exists(),
            "hardware": hardware,
            "error": None,
        }
    except (FileNotFoundError, ValueError, OSError, RuntimeError, ImportError, json.JSONDecodeError) as exc:
        try:
            device = _device()
        except (RuntimeError, ImportError):
            device = COLVISION_DEVICE
        return {
            "ready": False,
            "page_count": 0,
            "model": COLVISION_MODEL,
            "device": device,
            "scope": VISUAL_RAG_SCOPE,
            "model_prefetched": VISUAL_MODEL_READY_PATH.exists(),
            "hardware": hardware,
            "error": str(exc),
        }
