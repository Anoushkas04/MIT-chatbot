from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class CitationDetail(BaseModel):
    index: int = 0  # the [E<index>] marker in the answer text
    source: str  # document file name, or a label for non-document evidence
    title: str = ""  # readable name to show
    kind: str = "document"  # document | calendar | club | faculty | community
    snippet: str
    score: float
    document_id: Optional[str] = None
    page_number: Optional[int] = None
    retrieval_method: Optional[str] = None
    source_url: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    role: str = "student"
    language: str = "en"
    session_id: str = Field(min_length=1, max_length=128)
    department: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None

    @field_validator("message", "session_id")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class ChatResponse(BaseModel):
    text: str
    sources: List[str]
    citations: List[CitationDetail] = Field(default_factory=list)
    confidence: str
    confidence_type: str = "official_verified"  # "official_verified" | "community_grounded"
    followups: List[str] = Field(default_factory=list)
    provider: str = "local"
    model: str = "evidence-only"
    verification_warnings: List[str] = Field(default_factory=list)
    message_id: Optional[int] = None  # for rating the answer (POST /api/chat/feedback)
    searched_for: Optional[str] = None  # the corrected / translated / standalone search, if it differed
    question_count: int = 0
    response_count: int = 0
    demand_count: int = 0
    sample_size: int = 0


# --- Authentication & Profile Schemas ---

class RegisterSendOTPRequest(BaseModel):
    name: str
    registration_number: str
    learner_id: str


class RegisterVerifyOTPRequest(BaseModel):
    name: str
    registration_number: str
    learner_id: str
    otp_code: str
    agreed_terms: bool = False  # the Community Guidelines checkbox on the sign-up form
    terms_version: str = Field(default="", max_length=32)


class LoginSendOTPRequest(BaseModel):
    identifier: str  # Learner ID or 9-digit Registration Number


class LoginVerifyOTPRequest(BaseModel):
    identifier: str  # Learner ID or 9-digit Registration Number
    otp_code: str


