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
from app.rag.store import get_store

# Import all modular APIRouters
from app.routers.auth_router import router as auth_router
from app.routers.chat_router import router as chat_router
from app.routers.academic_router import router as academic_router
from app.routers.faculty_router import router as faculty_router
from app.routers.community_router import router as community_router
from app.routers.notifications_router import router as notifications_router
from app.routers.feedback_router import router as feedback_router
from app.routers.admin_router import router as admin_router
from app.routers.rewards_router import router as rewards_router
from app.routers.search_router import router as search_router

app = FastAPI(
    title="MIT CampusOS Platform API",
    description="Enterprise University AI Digital Operations Platform REST API for MIT Manipal (MAHE).",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(academic_router)
app.include_router(faculty_router)
app.include_router(community_router)
app.include_router(notifications_router)
app.include_router(feedback_router)
app.include_router(admin_router)
app.include_router(rewards_router)
app.include_router(search_router)


@app.on_event("startup")
def on_startup():
    try:
        seed_database()
        print("✓ MIT CampusOS Database initialized and seeded.")
    except Exception as e:
        print(f"Warning: Database seeding error: {e}")


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


@app.get("/api/health", tags=["0. System Health"])
def health():
    return {
        "status": "ok",
        "platform": "MIT CampusOS",
        "rag_store_ready": True,
        "docs_url": "http://localhost:8000/docs",
    }


@app.get("/api/departments", tags=["0. System Health"])
def get_departments():
    from app.database import SessionLocal
    from app import models
    db = SessionLocal()
    try:
        depts = db.query(models.Department).filter(models.Department.is_active == True).all()
        return {
            "count": len(depts),
            "departments": [
                {
                    "id": d.id,
                    "code": d.code,
                    "name": d.name,
                    "school": d.school,
                    "building": d.building,
                }
                for d in depts
            ],
        }
    finally:
        db.close()
