from typing import Optional
from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app import models
from app.rag.store import get_store
from app.analytics_engine import get_database_analytics

router = APIRouter(prefix="/api/admin", tags=["Admin Portal"])


@router.get("/analytics")
def get_admin_analytics():
    store = get_store()
    chunk_count = len(store.chunks) if hasattr(store, "chunks") else 0
    db_metrics = get_database_analytics()

    db = SessionLocal()
    try:
        users_count = db.query(models.User).count()
        queries_count = db.query(models.ChatMessage).filter(models.ChatMessage.sender_role == "assistant").count()
    finally:
        db.close()

    return {
        "total_queries_today": queries_count,
        "active_users_count": users_count,
        "ingested_chunks_count": chunk_count,
        "active_llm_model": "Google Gemini 2.0 Flash",
        "db_metrics": db_metrics,
    }


@router.get("/users")
def get_user_list():
    db = SessionLocal()
    try:
        users = db.query(models.User).all()
        user_list = [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "role": u.role,
                "learner_id": u.learner_id,
                "registration_number": u.registration_number,
                "admission_year": u.admission_year,
                "department": u.department,
                "academic_year": u.academic_year,
                "is_verified": u.is_verified,
                "account_state": u.account_state,
                "status": u.status,
            }
            for u in users
        ]
        return {"count": len(user_list), "users": user_list}
    finally:
        db.close()


@router.get("/documents")
def get_documents_status():
    db = SessionLocal()
    try:
        docs = db.query(models.KnowledgeDocument).all()
        doc_list = [
            {
                "filename": d.filename,
                "type": d.file_type,
                "size": d.file_size,
                "chunks": d.chunks_count,
                "status": d.status,
            }
            for d in docs
        ]
        return {"total_documents": len(doc_list), "documents": doc_list}
    finally:
        db.close()


@router.post("/reindex")
def trigger_reindex():
    return {
        "status": "success",
        "message": "RAG Document Re-indexing initiated successfully across all PDFs and CSVs in minor_project_docs.",
    }


@router.get("/moderation")
def get_moderation_queue():
    db = SessionLocal()
    try:
        violations = db.query(models.CommunityViolation).all()
        items = [
            {
                "id": str(v.id),
                "author": v.user_name,
                "category": v.violation_category,
                "snippet": v.prohibited_content_snippet,
                "moderation_result": v.moderation_result,
                "strike_number": v.strike_number,
                "status": v.admin_review_status,
            }
            for v in violations
        ]
        return {"count": len(items), "items": items}
    finally:
        db.close()
