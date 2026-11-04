import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.config import COLVISION_MODEL, DATA_DIR


BASE_MODEL = "vidore/ColSmolVLM-Instruct-500M-base"


def prefetch_visual_model(max_workers: int = 1, timeout: int = 300) -> dict:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = str(timeout)
    token = os.environ.get("HF_TOKEN") or None
    if not token:
        print("Warning: HF_TOKEN is not set; anonymous Hub rate limits may interrupt the download.")

    # Import after configuring the Hub transport environment.
    from huggingface_hub import snapshot_download

    snapshots = {}
    for repo_id in (BASE_MODEL, COLVISION_MODEL):
        print(f"Downloading {repo_id} with {max_workers} worker(s)...")
        snapshots[repo_id] = snapshot_download(
            repo_id=repo_id,
            token=token,
            max_workers=max_workers,
        )

    # The PEFT adapter repository contains processor/tokenizer files but no
    # config.json. Transformers v5 needs that config when loading fully
    # offline, so materialize it from the matching base snapshot.
    adapter_snapshot = Path(snapshots[COLVISION_MODEL])
    base_snapshot = Path(snapshots[BASE_MODEL])
    compatibility_config = adapter_snapshot / "config.json"
    if not compatibility_config.exists():
        shutil.copy2(base_snapshot / "config.json", compatibility_config)

    result = {
        "ready": True,
        "model": COLVISION_MODEL,
        "base_model": BASE_MODEL,
        "snapshots": snapshots,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "authenticated": bool(token),
        "offline_compatibility_config": str(compatibility_config),
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    from app.rag.visual_store import VISUAL_MODEL_READY_PATH
    VISUAL_MODEL_READY_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description="Reliably prefetch the ColSmol model and its PEFT base checkpoint.")
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if args.max_workers < 1:
        parser.error("--max-workers must be at least 1")
    print(json.dumps(prefetch_visual_model(args.max_workers, args.timeout), indent=2))


if __name__ == "__main__":
    main()
