from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Header, HTTPException
from app.database import SessionLocal
from app import models

router = APIRouter(prefix="/api/rewards", tags=["9. Student Rewards & Reputation"])


@router.get("/me", summary="Fetch current student's reputation score and badges portfolio")
def get_user_rewards(authorization: Optional[str] = Header(None)):
    if not authorization:
        return {
            "name": "Guest",
            "campus_points": 0,
            "rank": "N/A",
            "unlocked_badges_count": 0,
            "total_badges_count": 0,
            "badges": [],
            "activity_log": [],
        }

    token = authorization.replace("Bearer ", "").strip()
    from app.routers.auth_router import TOKENS_STORE
    user_id = TOKENS_STORE.get(token)

    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first() if user_id else None
        if not user:
            return {
                "name": "Student",
                "campus_points": 0,
                "rank": "N/A",
                "unlocked_badges_count": 0,
                "total_badges_count": 0,
                "badges": [],
                "activity_log": [],
            }

        badges_query = db.query(models.UserBadge).filter(models.UserBadge.user_id == user.id).all()
        badges_list = [
            {
                "id": str(b.id),
                "name": b.badge_name,
                "icon": b.badge_icon,
                "description": b.description,
                "unlocked": True,
                "unlocked_date": b.awarded_at.strftime("%b %d, %Y") if b.awarded_at else "Unlocked",
            }
            for b in badges_query
        ]

        return {
            "user_id": user.id,
            "name": user.name,
            "campus_points": user.rewards_points or 0,
            "rank": "Member",
            "unlocked_badges_count": len(badges_list),
            "total_badges_count": len(badges_list),
            "badges": badges_list,
            "activity_log": [],
        }
    finally:
        db.close()


@router.get("/leaderboard", summary="Get multi-period contributor leaderboard")
def get_leaderboard(timeframe: str = "weekly"):
    db = SessionLocal()
    try:
        users = (
            db.query(models.User)
            .filter(models.User.role == "student")
            .order_by(models.User.rewards_points.desc())
            .limit(10)
            .all()
        )
        leaderboard = [
            {
                "rank": idx + 1,
                "name": u.name,
                "dept": f"{u.department or 'MIT'} ({u.academic_year or 'Student'})",
                "points": u.rewards_points or 0,
                "helpful_answers": 0,
                "badge": "🎓 Verified Student" if u.is_verified else "🎓 Member",
            }
            for idx, u in enumerate(users)
        ]
        return {
            "timeframe": timeframe,
            "leaderboard": leaderboard,
        }
    finally:
        db.close()
