import os
import sys

# Windows' console defaults stdout/stderr to a non-UTF-8 codepage, which crashes
# any print()/log call containing emoji (used throughout this codebase) with
# UnicodeEncodeError. Force UTF-8 at the process entrypoint, once, for everyone.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.seed import seed_database
from app.rag.store import get_store_status

# Import all modular APIRouters
from app.routers.auth_router import router as auth_router
from app.routers.chat_router import router as chat_router
from app.routers.admin_router import router as admin_router
from app.routers.library_router import router as library_router
from app.routers.users_router import router as users_router
from app.routers.community_v2 import router as community_v2_router
from app.routers.admin_community import router as admin_community_router
from app.routers.me_router import router as me_router
from app.routers.admin_safety import router as admin_safety_router
from app.routers.admin_dataset import router as admin_dataset_router
from app.routers.admin_insights import router as admin_insights_router
from app.routers.network_router import messages_router, router as network_router
from app.routers.directory_router import router as directory_router

app = FastAPI(
    title="MIT CampusOS Platform API",
    description="Enterprise University AI Digital Operations Platform REST API for MIT Manipal (MAHE).",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Only the MITra frontend may call the API from a browser. Auth is a Bearer token, not a
# cookie, so credentials aren't needed. Add other origins (e.g. a LAN address or the
# deployed site) with CORS_ORIGINS=https://a.example,http://192.168.1.5:3000
_cors_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()] or [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(library_router)
app.include_router(users_router)
app.include_router(community_v2_router)
app.include_router(admin_community_router)
app.include_router(me_router)
app.include_router(admin_safety_router)
app.include_router(admin_dataset_router)
app.include_router(admin_insights_router)
app.include_router(network_router)
app.include_router(messages_router)
app.include_router(directory_router)


@app.on_event("startup")
def on_startup():
    try:
        seed_database()
        print("✓ MIT CampusOS Database initialized and seeded.")
    except Exception as e:
        print(f"Warning: Database seeding error: {e}")
    _build_index_if_missing()


def _build_index_if_missing():
    """Without an index the chatbot can't search any document, so build one on first start."""
    from app import audit
    from app.config import DOCS_DIR
    from app.database import SessionLocal
    from app.rag import index

    if index.exists() or not DOCS_DIR.exists() or not any(p.is_file() for p in DOCS_DIR.iterdir()):
        return
    if index.rebuild_in_background():
        print("ℹ️  No chatbot index found: building it in the background.")
        db = SessionLocal()
        try:
            audit.record(db, None, "dataset.rebuild", "Started building the chatbot index automatically (none existed)", "index", None)
            db.commit()
        finally:
            db.close()


@app.get("/", tags=["0. System Health"])
def root():
    return {
        "status": "online",
        "name": "MIT CampusOS Platform API",
        "version": "2.0.0",
        "description": "Enterprise University AI Digital Operations Platform REST API for MIT Manipal (MAHE)",
        "docs": "http://localhost:8000/docs",
        "health": "http://localhost:8000/api/health",
        "stats": "http://localhost:8000/api/stats",
    }


def _ocr_status() -> dict:
    """What the last index build read from scanned pages (from its manifest)."""
    from app.rag.store import get_store

    try:
        manifest = get_store().manifest or {}
    except Exception:
        return {"scanned_pages": None, "ocr_pages": None}
    return {
        "scanned_pages": manifest.get("scanned_page_count"),
        "ocr_pages": manifest.get("ocr_page_count"),
        "ocr_chunks": manifest.get("ocr_chunk_count"),
        "calendar_events": manifest.get("calendar_event_count"),
    }


@app.get("/api/health", tags=["0. System Health"])
def health():
    rag = get_store_status()
    from app.providers import get_provider_status
    from app.rag.visual_store import get_visual_status
    from app.database import schema_status
    visual = get_visual_status()
    database = schema_status()
    return {
        "status": "ok" if rag["ready"] and database["ok"] else "degraded",
        "platform": "MIT CampusOS",
        "rag_store_ready": rag["ready"],
        "rag_chunk_count": rag["chunk_count"],
        "rag_error": rag["error"],
        "rag_embedder": rag.get("embedder"),
        "ocr": _ocr_status(),
        "database": database,
        "visual_rag": visual,
        "llm": get_provider_status(),
        "docs_url": "http://localhost:8000/docs",
    }
