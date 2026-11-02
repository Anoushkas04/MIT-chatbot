import json
from functools import lru_cache
from pathlib import Path

from app.config import COLVISION_DEVICE, COLVISION_MODEL, DATA_DIR


VISUAL_EMBEDDINGS_PATH = DATA_DIR / "visual_embeddings.pt"
VISUAL_MANIFEST_PATH = DATA_DIR / "visual_manifest.json"


def _device() -> str:
    import torch
    if COLVISION_DEVICE != "auto":
        return COLVISION_DEVICE
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache
def get_visual_model():
    from sentence_transformers import MultiVectorEncoder
    return MultiVectorEncoder(COLVISION_MODEL, device=_device())


def build_visual_index(pages: list[dict], image_root: Path, progress_callback=None) -> dict:
    import torch
    progress = progress_callback or (lambda percent, message: None)
    candidates = [page for page in pages if page.get("image_path")]
    if not candidates:
        raise RuntimeError("No rendered page images are available for visual indexing.")
    model = get_visual_model()
    embeddings = []
    batch_size = 1 if _device() == "cpu" else 2
    for start in range(0, len(candidates), batch_size):
        batch = candidates[start:start + batch_size]
        paths = [str(image_root / Path(page["image_path"]).name) for page in batch]
        encoded = model.encode_document(paths, batch_size=batch_size, convert_to_numpy=False, show_progress_bar=False)
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
    }, indent=2), encoding="utf-8")
    clear_visual_cache()
    return {"page_count": len(candidates), "model": COLVISION_MODEL, "device": _device()}


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
        scores = model.similarity(query_embeddings, self.embeddings).detach().cpu().reshape(-1)
        indices = torch.argsort(scores, descending=True)[:k]
        return [
            {**self.pages[int(index)], "score": float(scores[index]), "retrieval_method": "colvision"}
            for index in indices
        ]


@lru_cache
def get_visual_store() -> VisualStore:
    return VisualStore()


def clear_visual_cache() -> None:
    get_visual_store.cache_clear()


def get_visual_status() -> dict:
    try:
        store = get_visual_store()
        return {
            "ready": True,
            "page_count": len(store.pages),
            "model": store.manifest.get("model"),
            "device": _device(),
            "error": None,
        }
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as exc:
        return {"ready": False, "page_count": 0, "model": COLVISION_MODEL, "device": _device(), "error": str(exc)}
