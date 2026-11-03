import datetime
from typing import List, Dict, Any, Tuple
from app import models

COMMUNITY_GUIDELINES = [
    "1. Respectful Communication: No hate speech, harassment, or abusive language targeting students, faculty, or staff.",
    "2. Fact Accuracy: Ensure academic timetables, lab room numbers, and cutoff numbers are backed by verified experience.",
    "3. No Spam or Self-Promotion: Commercial ads, paid promotion, or duplicate spam posts will be quarantined immediately.",
    "4. Report Outdated Info: Help keep CampusOS fresh by flagging outdated mess timings or obsolete circulars.",
    "5. Maintain Confidentiality: Do not leak unannounced grading sheets or private faculty contact info.",
]

# Prohibited Content Pattern Dictionary
PROHIBITED_CATEGORIES = {
    "Explicit Sexual Content": [
        "nsfw", "porn", "explicit sex", "erotic content", "sexual exploitation", "nude leak", "pornography"
    ],
    "Harassment & Targeted Abuse": [
        "kill yourself", "threaten to leak", "dox", "die bitch", "harass professor", "target student", "stalk", "abuse student"
    ],
    "Hate Speech": [
        "slur", "hate speech", "racist attack", "casteist insult", "bigoted attack", "hate group"
    ],
    "Illegal Activity & Substances": [
        "buy weed campus", "sell drugs hostel", "fake hall ticket forge", "hack portal server", "buy illegal drugs", "substance abuse sale", "cheat exam leak paper"
    ]
}

# Academic / Harmless Context Whitelist Keywords (To avoid false positives in legitimate academic discussions)
ACADEMIC_SAFE_TERMS = [
    "chemistry", "pharmacology", "legal", "law", "study", "research", "paper", "lab experiment", "cybersecurity", "security test", "ethical hacking class"
]


def evaluate_community_content(title: str, content: str) -> Tuple[bool, str, str, float]:
    """Pre-Publish Moderation Evaluator

    Analyzes title and content for prohibited community violations.
    Returns (is_prohibited, violation_category, reason, confidence).
    """
    if not title and not content:
        return False, "None", "Clean", 0.0

    text_combined = f"{title} {content}".lower()

    # Check if this is a legitimate academic discussion
    is_academic_context = any(term in text_combined for term in ACADEMIC_SAFE_TERMS)

    for category, keywords in PROHIBITED_CATEGORIES.items():
        for kw in keywords:
            if kw in text_combined:
                # If keyword matches, ensure it's not a safe academic usage
                if is_academic_context and category == "Illegal Activity & Substances" and "illegal" not in kw and "sell" not in kw:
                    continue  # Safe academic context
                return True, category, f"Detected prohibited patterns ({category})", 0.95

    return False, "Clean", "Content complies with community guidelines", 0.10


def process_user_strike_and_suspension(db, user_identifier: str, user_name: str, violation_cat: str, snippet: str) -> Dict[str, Any]:
    """Records a community violation, increments user strike count, and enforces 7-day suspension upon 5th strike."""
    user = None
    if user_identifier:
        user = db.query(models.User).filter((models.User.id == user_identifier) | (models.User.name == user_name)).first()

    # Create demo student user if not found in db
    if not user:
        clean_id = f"user_{hash(user_name) % 10000}"
        user = models.User(
            id=clean_id,
            email=f"{clean_id}@manipal.edu",
            password_hash="demo_hash",
            name=user_name,
            role="student",
            strike_count=0,
            is_suspended=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Increment Strike Count
    user.strike_count += 1
    current_strikes = user.strike_count

    # Check 5th Strike Suspension Rule (7 Days)
    is_suspended_now = False
    suspended_until = None
    if user.strike_count >= 5:
        user.is_suspended = True
        user.suspended_at = datetime.datetime.utcnow()
        user.suspended_until = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        is_suspended_now = True
        suspended_until = user.suspended_until

    # Record Violation in DB
    violation = models.CommunityViolation(
        user_id=user.id,
        user_name=user_name,
        violation_category=violation_cat,
        prohibited_content_snippet=snippet[:300],
        moderation_result="Blocked Pre-Publish & Strike Recorded",
        strike_number=current_strikes,
        admin_review_status="Pending Admin Review",
    )
    db.add(violation)
    db.commit()
    db.refresh(user)

    return {
        "user_id": user.id,
        "strike_count": current_strikes,
        "is_suspended": user.is_suspended,
        "suspended_until": user.suspended_until,
    }


def check_user_suspension_status(db, user_identifier: str) -> Tuple[bool, str, Any]:
    """Checks if a user is currently suspended and automatically restores access after 7 days."""
    if not user_identifier:
        return False, "", None

    user = db.query(models.User).filter((models.User.id == user_identifier) | (models.User.name == user_identifier)).first()
    if not user or not user.is_suspended:
        return False, "", None

    now = datetime.datetime.utcnow()

    # Automatic Restoration Rule after 7 Days Expiry
    if user.suspended_until and now >= user.suspended_until:
        user.is_suspended = False
        user.suspended_until = None
        user.suspended_at = None
        db.commit()
        return False, "Suspension expired. Community access automatically restored.", None

    until_str = user.suspended_until.strftime("%b %d, %Y") if user.suspended_until else "7 days"
    msg = f"⚠️ Your account is currently suspended from community posting until {until_str} due to repeated guideline violations."
    return True, msg, user.suspended_until


def get_reported_items() -> List[Dict[str, Any]]:
    """Moderation Engine: Tracks reported posts/comments, student outdated alerts,
    content status, and user reputation penalties.
    """
    return [
        {
            "id": "rep_01",
            "type": "Community Post",
            "title": "Block 13 Mess Dinner Closing Hours",
            "author": "Rohan Mehta",
            "author_reputation": "420 Campus Points",
            "reports_count": 8,
            "primary_reason": "Outdated Information",
            "status": "Flagged for Review",
            "student_alert": "⚠️ Students have reported that this information may be outdated.",
            "snippet": "Mess dinner entry gate is open till 9:30 PM everyday without exception.",
            "timestamp": "3 hours ago",
        },
        {
            "id": "rep_02",
            "type": "Community Answer",
            "title": "Re: AB5 Basement Printing Machine Charges",
            "author": "Karan Malhotra",
            "author_reputation": "110 Campus Points",
            "reports_count": 4,
            "primary_reason": "Flag Misinformation",
            "status": "Flagged for Review",
            "student_alert": "⚠️ Students have reported that printing charges mentioned here are incorrect.",
            "snippet": "Printing costs ₹5 per page for black and white at AB5 basement.",
            "timestamp": "6 hours ago",
        },
        {
            "id": "rep_03",
            "type": "Community Post",
            "title": "Join Off-Campus Party Group Link",
            "author": "AnonUser99",
            "author_reputation": "0 Campus Points",
            "reports_count": 12,
            "primary_reason": "Spam / Advertising",
            "status": "Quarantined",
            "student_alert": "🚫 Automatically quarantined by AI Spam Filter.",
            "snippet": "Click this link to join external party chat group...",
            "timestamp": "12 hours ago",
        },
        {
            "id": "rep_04",
            "type": "Community Answer",
            "title": "Re: Quiet Floor Rules in Central Library",
            "author": "Ananya Sen",
            "author_reputation": "890 Campus Points",
            "reports_count": 0,
            "primary_reason": "Clean",
            "status": "Approved",
            "student_alert": "✓ Verified accurate by 45 student votes.",
            "snippet": "3rd floor is strict silence zone; 1st floor allows group discussion.",
            "timestamp": "1 day ago",
        },
    ]
