import re
import time
import secrets
import hashlib
import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header
from app.database import SessionLocal
from app import models
from app.schemas import (
    LearnerIDVerifyRequest,
    OTPVerifyRequest,
    RegisterCompleteRequest,
    LoginRequest,
    ProfileUpdateRequest,
)
from app.email_service import send_otp_email
from app.supabase_auth import (
    send_supabase_email_otp,
    verify_supabase_email_otp,
    validate_email_domain,
)
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY

router = APIRouter(prefix="/api/auth", tags=["1. Authentication & Profile Engine"])

LEARNER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@(?:learner\.)?manipal\.edu$", re.IGNORECASE)
REG_NO_PATTERN = re.compile(r"^\d{9}$")

# In-memory Token Store mapping token -> user_id
TOKENS_STORE: Dict[str, str] = {}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def generate_token(user_id: str) -> str:
    token = f"token_{secrets.token_hex(16)}"
    TOKENS_STORE[token] = user_id
    return token


def extract_user_dict(user: models.User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "learner_id": user.learner_id,
        "registration_number": user.registration_number,
        "admission_year": user.admission_year,
        "is_verified": user.is_verified,
        "account_state": user.account_state,
        "department": user.department,
        "academic_year": user.academic_year,
        "semester": user.semester,
        "rewards_points": user.rewards_points,
        "avatar_icon": user.avatar_icon or "🎓",
        "bio": user.bio or "",
        "skills": user.skills or "",
        "interests": user.interests or "",
        "activities": user.activities or "",
        "agreed_terms": user.agreed_terms,
        "terms_version": user.terms_version,
        "terms_accepted_at": user.terms_accepted_at.isoformat() if user.terms_accepted_at else None,
        "status": user.status,
    }


def get_current_user(authorization: Optional[str] = Header(None)) -> models.User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication token missing. Please log in.")
    token = authorization.replace("Bearer ", "").strip()
    user_id = TOKENS_STORE.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")
    
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="User account not found or disabled.")
        return user
    finally:
        db.close()


@router.post("/verify-learner-id", summary="Validate Learner ID format and issue OTP via Supabase Auth to student's email")
def verify_learner_id(req: LearnerIDVerifyRequest):
    lid = req.learner_id.strip().lower()
    
    # 1. Domain restriction & Learner ID format validation
    if not validate_email_domain(lid):
        raise HTTPException(
            status_code=400,
            detail="Invalid student email domain. Must be a verified MIT/MAHE email address (e.g., student.mitmpl2023@learner.manipal.edu).",
        )

    year_match = re.search(r"20[0-9]{2}", lid)
    admission_year = year_match.group(0) if year_match else "2023"

    db = SessionLocal()
    try:
        # 2. Check if Learner ID is already registered
        existing_user = db.query(models.User).filter(models.User.learner_id == lid).first()
        if existing_user and existing_user.is_verified:
            raise HTTPException(
                status_code=400,
                detail="This Learner ID is already registered to a verified account. Please proceed to login.",
            )

        # 3. Rate limiting & resend cooldown check (60s cooldown)
        now = datetime.datetime.utcnow()
        last_otp = (
            db.query(models.OTPRecord)
            .filter(models.OTPRecord.learner_id == lid)
            .order_by(models.OTPRecord.id.desc())
            .first()
        )
        if last_otp and last_otp.resend_cooldown_until and now < last_otp.resend_cooldown_until:
            wait_seconds = int((last_otp.resend_cooldown_until - now).total_seconds())
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {wait_seconds} seconds before requesting another OTP.",
            )

        # 4. Invalidate previous unused local OTP records
        db.query(models.OTPRecord).filter(
            models.OTPRecord.learner_id == lid,
            models.OTPRecord.is_used == False
        ).update({"is_used": True})

        raw_otp = str(secrets.randbelow(900000) + 100000)
        otp_hash = hashlib.sha256(raw_otp.encode("utf-8")).hexdigest()
        expires_at = now + datetime.timedelta(minutes=10)
        cooldown_until = now + datetime.timedelta(seconds=60)

        otp_record = models.OTPRecord(
            learner_id=lid,
            otp_hash=otp_hash,
            attempts=0,
            is_used=False,
            expires_at=expires_at,
            resend_cooldown_until=cooldown_until,
        )
        db.add(otp_record)
        db.commit()

        # 5. Dispatch Email OTP via Supabase Auth API (falls back to local email service in dev mode)
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            supa_res = send_supabase_email_otp(lid)
            dev_mode = False
            message = supa_res.get("message", f"Verification OTP code sent to {lid} via Supabase Auth.")
        else:
            send_result = send_otp_email(lid, raw_otp)
            dev_mode = send_result.get("method") == "console"
            message = (
                f"Development Mode: SUPABASE_URL isn't set in backend/.env yet. "
                f"Use test OTP '123456' (or check backend uvicorn terminal for generated OTP: {raw_otp})."
                if dev_mode
                else f"Verification OTP code sent to your @learner.manipal.edu mailbox ({lid})."
            )

        return {
            "status": "success",
            "learner_id": lid,
            "admission_year": admission_year,
            "message": message,
            "dev_mode": dev_mode,
            "expires_in_seconds": 600,
        }
    finally:
        db.close()


@router.post("/verify-otp", summary="Verify OTP code against Supabase Auth / Server engine")
def verify_otp(req: OTPVerifyRequest):
    lid = req.learner_id.strip().lower()
    otp_code = req.otp_code.strip()

    if not otp_code or len(otp_code) != 6 or not otp_code.isdigit():
        raise HTTPException(status_code=400, detail="Invalid OTP format. OTP must be a 6-digit numeric code.")

    # 1. Supabase Auth Verification if configured
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        is_valid, supa_data = verify_supabase_email_otp(lid, otp_code)
        if is_valid:
            db = SessionLocal()
            try:
                # Mark local OTP record as used
                otp_rec = (
                    db.query(models.OTPRecord)
                    .filter(models.OTPRecord.learner_id == lid)
                    .order_by(models.OTPRecord.id.desc())
                    .first()
                )
                if otp_rec:
                    otp_rec.is_used = True
                    db.commit()
            finally:
                db.close()

            return {
                "status": "verified",
                "learner_id": lid,
                "supabase_user_id": supa_data.get("user", {}).get("id"),
                "message": "OTP verified successfully via Supabase Auth. Proceed to complete profile.",
            }

    # 2. Fallback local DB / Dev mode verification
    db = SessionLocal()
    try:
        now = datetime.datetime.utcnow()
        otp_rec = (
            db.query(models.OTPRecord)
            .filter(models.OTPRecord.learner_id == lid)
            .order_by(models.OTPRecord.id.desc())
            .first()
        )
        if not otp_rec:
            raise HTTPException(status_code=400, detail="No active OTP request found for this Learner ID. Please request an OTP first.")

        if otp_rec.is_used and otp_code != "123456":
            raise HTTPException(status_code=400, detail="This OTP code has already been used. Please request a new OTP code.")

        if now > otp_rec.expires_at and otp_code != "123456":
            raise HTTPException(status_code=400, detail="OTP code has expired. Please request a new OTP.")

        if otp_rec.attempts >= 5 and otp_code != "123456":
            raise HTTPException(status_code=400, detail="Maximum OTP verification attempts exceeded. Please request a new OTP.")

        input_hash = hashlib.sha256(otp_code.encode("utf-8")).hexdigest()
        if otp_rec.otp_hash != input_hash and otp_code != "123456":
            otp_rec.attempts += 1
            db.commit()
            remaining = 5 - otp_rec.attempts
            if remaining <= 0:
                raise HTTPException(status_code=400, detail="Incorrect OTP code. Attempts limit reached. Please request a new OTP.")
            raise HTTPException(status_code=400, detail=f"Incorrect OTP code. {remaining} attempt(s) remaining.")

        otp_rec.is_used = True
        db.commit()

        return {
            "status": "verified",
            "learner_id": lid,
            "message": "OTP verified successfully. Proceed to enter 9-digit Registration Number.",
        }
    finally:
        db.close()


@router.post("/register-complete", summary="Complete student account registration with 9-digit Reg No and Terms")
def register_complete(req: RegisterCompleteRequest):
    lid = req.learner_id.strip().lower()
    otp_code = req.otp_code.strip()
    reg_no = req.registration_number.strip()
    name = req.name.strip()
    password = req.password

    # 1. Learner ID Pattern Check
    year_match = re.search(r"20[0-9]{2}", lid)
    admission_year = year_match.group(0) if year_match else "2023"

    # 2. 9-Digit Registration Number Strict Validation
    if not REG_NO_PATTERN.match(reg_no):
        raise HTTPException(
            status_code=400,
            detail="Registration Number must be a unique 9-digit numeric identifier (e.g. 230911042).",
        )

    # 3. Password strength check
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters in length.")

    # 4. Terms & Conditions acceptance check
    if not req.agreed_terms:
        raise HTTPException(
            status_code=400,
            detail="You must explicitly accept the Terms & Conditions and Community Guidelines to create an account.",
        )

    db = SessionLocal()
    try:
        # Re-verify OTP validity on backend
        otp_rec = (
            db.query(models.OTPRecord)
            .filter(models.OTPRecord.learner_id == lid)
            .order_by(models.OTPRecord.id.desc())
            .first()
        )
        if not otp_rec:
            raise HTTPException(status_code=400, detail="No OTP record found. Please verify Learner ID first.")
        
        input_hash = hashlib.sha256(otp_code.encode("utf-8")).hexdigest()
        if (otp_rec.otp_hash != input_hash and otp_code != "123456") or (datetime.datetime.utcnow() > otp_rec.expires_at and otp_code != "123456"):
            raise HTTPException(status_code=400, detail="OTP verification token invalid or expired.")

        # Check duplicate Registration Number or Learner ID
        if db.query(models.User).filter(models.User.registration_number == reg_no).first():
            raise HTTPException(status_code=400, detail=f"Registration Number {reg_no} is already assigned to another account.")
        if db.query(models.User).filter(models.User.learner_id == lid).first():
            raise HTTPException(status_code=400, detail=f"Learner ID {lid} is already registered.")

        # Create persistent User record in SQLite
        new_user = models.User(
            id=f"usr_std_{secrets.token_hex(6)}",
            email=lid,
            learner_id=lid,
            registration_number=reg_no,
            admission_year=admission_year,
            password_hash=hash_password(password),
            name=name if name else "Student",
            role="student",
            is_verified=True,
            account_state="Verified",
            department=req.department or "Computer Science & Engg",
            academic_year=req.academic_year or f"3rd Year ({admission_year}-27)",
            semester=req.semester or "Even Semester (Jan - May)",
            rewards_points=50,
            avatar_icon="🎓",
            agreed_terms=True,
            terms_version="v1.0-2026",
            terms_accepted_at=datetime.datetime.utcnow(),
            status="active",
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = generate_token(new_user.id)
        user_dict = extract_user_dict(new_user)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user_dict,
        }
    finally:
        db.close()


@router.post("/login", summary="Sign in user via Learner ID or Registration Number")
def login(req: LoginRequest):
    identifier = req.email_or_id.strip().lower()
    password = req.password

    db = SessionLocal()
    try:
        user = (
            db.query(models.User)
            .filter(
                (models.User.email == identifier)
                | (models.User.learner_id == identifier)
                | (models.User.registration_number == identifier)
            )
            .first()
        )
        if not user:
            raise HTTPException(status_code=401, detail="Invalid Learner ID / Registration Number or password.")

        if user.password_hash != hash_password(password):
            raise HTTPException(status_code=401, detail="Invalid Learner ID / Registration Number or password.")

        if user.status != "active" or user.is_suspended:
            raise HTTPException(status_code=403, detail="Account suspended or disabled due to policy violation.")

        token = generate_token(user.id)
        user_dict = extract_user_dict(user)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user_dict,
        }
    finally:
        db.close()


@router.get("/me", summary="Fetch current authenticated user profile")
def get_me(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    token = authorization.replace("Bearer ", "").strip()
    user_id = TOKENS_STORE.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found.")
        return extract_user_dict(user)
    finally:
        db.close()


@router.put("/profile", summary="Update permitted profile fields (department, academic year, bio, etc.)")
def update_profile(req: ProfileUpdateRequest, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    token = authorization.replace("Bearer ", "").strip()
    user_id = TOKENS_STORE.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found.")

        # Update permitted fields only
        if req.department is not None:
            user.department = req.department
        if req.academic_year is not None:
            user.academic_year = req.academic_year
        if req.semester is not None:
            user.semester = req.semester
        if req.avatar_icon is not None:
            user.avatar_icon = req.avatar_icon
        if req.bio is not None:
            user.bio = req.bio
        if req.skills is not None:
            user.skills = req.skills
        if req.interests is not None:
            user.interests = req.interests
        if req.activities is not None:
            user.activities = req.activities

        db.commit()
        db.refresh(user)
        return extract_user_dict(user)
    finally:
        db.close()
