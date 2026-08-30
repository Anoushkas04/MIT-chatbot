from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class CitationDetail(BaseModel):
    source: str
    snippet: str
    score: float


class ChatRequest(BaseModel):
    message: str
    role: str = "student"
    language: str = "en"
    session_id: str
    department: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None


class ChatResponse(BaseModel):
    text: str
    sources: List[str]
    citations: List[CitationDetail] = []
    confidence: str
    confidence_type: str = "official_verified"  # "official_verified" | "community_grounded"
    followups: List[str] = []
    question_count: int = 0
    response_count: int = 0
    demand_count: int = 0
    sample_size: int = 0


# --- Authentication & Profile Schemas ---

class LearnerIDVerifyRequest(BaseModel):
    learner_id: str


class OTPVerifyRequest(BaseModel):
    learner_id: str
    otp_code: str


class RegisterCompleteRequest(BaseModel):
    learner_id: str
    otp_code: str
    registration_number: str
    password: str
    name: str
    department: Optional[str] = "Computer Science & Engg"
    academic_year: Optional[str] = "3rd Year (2023-27)"
    semester: Optional[str] = "Even Semester (Jan - May)"
    agreed_terms: bool = True


class LoginRequest(BaseModel):
    email_or_id: str
    password: str


class ProfileUpdateRequest(BaseModel):
    department: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    avatar_icon: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[str] = None
    interests: Optional[str] = None
    activities: Optional[str] = None


