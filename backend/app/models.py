import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="student")  # student, faculty, parent, admin
    learner_id = Column(String, unique=True, index=True, nullable=True)
    registration_number = Column(String, unique=True, index=True, nullable=True)
    admission_year = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    account_state = Column(String, default="Pending Verification")  # Pending Verification, Verified, Suspended, Deactivated
    department = Column(String, nullable=True)
    academic_year = Column(String, nullable=True)
    semester = Column(String, nullable=True)
    rewards_points = Column(Integer, default=0)
    avatar_icon = Column(String, default="🎓")
    bio = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    interests = Column(Text, nullable=True)
    activities = Column(Text, nullable=True)
    status = Column(String, default="active")
    strike_count = Column(Integer, default=0)
    is_suspended = Column(Boolean, default=False)
    suspended_at = Column(DateTime, nullable=True)
    suspended_until = Column(DateTime, nullable=True)
    agreed_terms = Column(Boolean, default=False)
    terms_version = Column(String, default="v1.0-2026")
    terms_accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("StudentPost", back_populates="author", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    violations = relationship("CommunityViolation", back_populates="user", cascade="all, delete-orphan")


class AuthorizedStudent(Base):
    __tablename__ = "authorized_students"

    learner_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    department = Column(String, default="Computer Science & Engg")
    academic_year = Column(String, default="3rd Year (2023-27)")
    mobile = Column(String, default="+91 98******42")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    school = Column(String, default="School of Computing")
    building = Column(String, default="Academic Block 5 (AB5)")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class OTPRecord(Base):
    __tablename__ = "otp_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    learner_id = Column(String, nullable=False, index=True)
    otp_hash = Column(String, nullable=False)
    attempts = Column(Integer, default=0)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    resend_cooldown_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class CommunityViolation(Base):
    __tablename__ = "community_violations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    user_name = Column(String, nullable=False)
    violation_category = Column(String, nullable=False)  # Explicit Content, Harassment, Illegal Activity, Hate Speech
    prohibited_content_snippet = Column(Text, nullable=False)
    moderation_result = Column(String, default="Blocked Pre-Publish")
    strike_number = Column(Integer, default=1)
    admin_review_status = Column(String, default="Pending Admin Review")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="violations")


class AcademicEvent(Base):
    __tablename__ = "academic_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, default="Exams")  # Exams, Deadlines, Academic, Holidays, Clubs, Workshops, Hackathons, Placements, Financial, General
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    notification_offsets = Column(Text, default="[10080, 4320, 1440, 60, 0]")  # Offset thresholds in minutes (7d, 3d, 24h, 1h, 0m)
    target_audience = Column(String, default="all")  # all, student, faculty, parent, admin
    department = Column(String, default="all")  # all or specific department name/code
    academic_year = Column(String, default="all")  # all or 1st Year (2025-29), 2nd Year (2024-28), 3rd Year (2023-27), 4th Year (2022-26)
    semester = Column(String, default="all")  # all, Odd Semester (Jul - Dec), Even Semester (Jan - May)
    priority = Column(String, default="NORMAL")  # NORMAL, HIGH, URGENT
    source = Column(String, default="Official MIT Academic Calendar")
    status = Column(String, default="published")  # published, draft
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class UserNotificationState(Base):
    __tablename__ = "user_notification_states"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    event_id = Column(Integer, ForeignKey("academic_events.id"), nullable=False)
    offset_minutes = Column(Integer, nullable=False)
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    is_popup_dismissed = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    event = relationship("AcademicEvent")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    icon = Column(String, default="📢")
    title = Column(String, nullable=False)
    time = Column(String, default="Just now")
    category = Column(String, default="Academic")
    type_color = Column(String, default="blue")
    content = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String, nullable=False, unique=True)
    file_type = Column(String, nullable=False)
    file_size = Column(String, nullable=False)
    chunks_count = Column(Integer, default=0)
    status = Column(String, default="Indexed & Vectorized")
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    role = Column(String, default="student")
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    sender_role = Column(String, nullable=False)  # user, assistant
    text = Column(Text, nullable=False)
    confidence = Column(String, default="high")
    confidence_type = Column(String, default="official_verified")
    timestamp = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
    citations = relationship("MessageCitation", back_populates="message", cascade="all, delete-orphan")


class MessageCitation(Base):
    __tablename__ = "message_citations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False)
    source_name = Column(String, nullable=False)
    snippet = Column(Text, nullable=True)
    similarity_score = Column(Float, default=0.0)

    message = relationship("ChatMessage", back_populates="citations")


class StudentPost(Base):
    __tablename__ = "student_posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    author_id = Column(String, ForeignKey("users.id"), nullable=True)
    author_name = Column(String, nullable=False)
    sub_community = Column(String, default="Hostel & Mess")
    tag = Column(String, default="General")
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    upvotes = Column(Integer, default=1)
    downvotes = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    time = Column(String, default="Just now")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    author = relationship("User", back_populates="posts")
    comments = relationship("PostComment", back_populates="post", cascade="all, delete-orphan")


class PostComment(Base):
    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("student_posts.id"), nullable=False)
    author_name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    is_helpful = Column(Boolean, default=False)
    upvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    post = relationship("StudentPost", back_populates="comments")


class PostUpvote(Base):
    __tablename__ = "post_upvotes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("student_posts.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    badge_name = Column(String, nullable=False)
    badge_icon = Column(String, default="🏆")
    description = Column(String, nullable=False)
    awarded_at = Column(DateTime, default=datetime.datetime.utcnow)


class SystemFeedback(Base):
    __tablename__ = "system_feedback"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    feedback_type = Column(String, default="General")
    message = Column(Text, nullable=False)
    rating = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ModerationRecord(Base):
    __tablename__ = "moderation_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, nullable=True)
    admin_id = Column(String, nullable=False)
    action = Column(String, nullable=False)  # approved, rejected, flagged
    reason = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class LearningSignal(Base):
    __tablename__ = "learning_signals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    resolved_source = Column(String, nullable=True)
    confidence_score = Column(Float, default=0.0)
    explicit_rating = Column(Integer, default=1)  # +1 for helpful, -1 for unhelpful
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class KnowledgeGap(Base):
    __tablename__ = "knowledge_gaps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    topic = Column(String, default="General")
    category = Column(String, default="Academics")
    frequency = Column(Integer, default=1)
    avg_confidence = Column(Float, default=0.0)
    community_answers_count = Column(Integer, default=0)
    has_official_source = Column(Boolean, default=False)
    status = Column(String, default="unresolved")  # unresolved, in_review, verified
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class QueryAnalyticsLog(Base):
    __tablename__ = "query_analytics_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    topic = Column(String, default="General")
    intent = Column(String, default="academic_official")
    query_type = Column(String, default="simple_factual")
    sentiment = Column(String, default="Neutral")  # Positive, Neutral, Negative, Frustrated, Confused, Urgent
    entity = Column(String, nullable=True)
    confidence = Column(String, default="high")
    source_type = Column(String, default="official")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
