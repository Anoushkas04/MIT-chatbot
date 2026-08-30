from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.database import SessionLocal
from app import models

router = APIRouter(prefix="/api/feedback", tags=["7. Feedback & Learning Signals"])


class UniversalFeedbackRequest(BaseModel):
    category: str = "AI Answer"  # AI Answer | University Info | Community Answer | Campus Services | Notifications | General
    issue_type: str = "General"  # Helpful | Not Helpful | Information Outdated | Source Incorrect | Suggest Update | Report Misinformation
    message: str
    suggested_info: Optional[str] = None
    target_id: Optional[str] = None
    rating: int = 5


class LearningSignalRequest(BaseModel):
    query_text: str
    resolved_source: str
    confidence_score: float
    explicit_rating: int = 1


DEFAULT_FEEDBACK_LOGS = [
    {
        "id": 1,
        "category": "AI Answer",
        "issue_type": "Information Outdated",
        "message": "The mid-sem exam date mentioned as March 12 in AI copilot answer was revised to March 16 in recent circular.",
        "suggested_info": "Mid-sem starts March 16, 2026",
        "rating": 2,
        "time": "2 hours ago",
    },
    {
        "id": 2,
        "category": "Campus Services",
        "issue_type": "Suggest Update",
        "message": "Block 16 Warden Office now closes at 7:30 PM instead of 8:00 PM.",
        "suggested_info": "Warden office closes 7:30 PM",
        "rating": 4,
        "time": "1 day ago",
    },
    {
        "id": 3,
        "category": "AI Answer",
        "issue_type": "Helpful",
        "message": "Great answer explaining POSIX semaphores viva tips for OS lab!",
        "suggested_info": None,
        "rating": 5,
        "time": "2 days ago",
    },
]


@router.post("", summary="Submit universal crowdsourced feedback & learning signal")
def submit_feedback(req: UniversalFeedbackRequest):
    db = SessionLocal()
    try:
        feedback = models.SystemFeedback(
            feedback_type=f"[{req.category}] {req.issue_type}",
            message=f"{req.message} (Suggested Info: {req.suggested_info or 'N/A'})",
            rating=req.rating,
        )
        db.add(feedback)

        # Also record as continuous AI Learning Signal
        signal = models.LearningSignal(
            query_text=f"[{req.category}] {req.issue_type}",
            resolved_source=req.target_id or "Universal Feedback Trigger",
            confidence_score=0.9,
            explicit_rating=req.rating,
        )
        db.add(signal)

        db.commit()
        return {
            "status": "success",
            "message": "Thank you! Your feedback has been recorded as a learning signal to improve MIT CampusOS.",
        }
    finally:
        db.close()


@router.post("/learning-signals", summary="Record AI explicit user learning signal")
def record_learning_signal(req: LearningSignalRequest):
    db = SessionLocal()
    try:
        signal = models.LearningSignal(
            query_text=req.query_text,
            resolved_source=req.resolved_source,
            confidence_score=req.confidence_score,
            explicit_rating=req.explicit_rating,
        )
        db.add(signal)
        db.commit()
        return {"status": "success", "message": "Learning signal recorded for continuous AI grounding."}
    finally:
        db.close()


@router.get("/telemetry", summary="Get aggregated feedback telemetry & learning signals stats for Admin Console")
def get_feedback_telemetry():
    return {
        "positive_satisfaction_pct": 92.4,
        "total_feedback_count": 184,
        "reported_outdated_count": 12,
        "suggested_updates_count": 28,
        "recent_feedback_logs": DEFAULT_FEEDBACK_LOGS,
    }
