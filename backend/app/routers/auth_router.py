import re
import hmac
import secrets
import hashlib
import datetime
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from app.database import SessionLocal
from app import models
from app.schemas import (
    ProfileUpdateRequest,
    RegisterSendOTPRequest,
    RegisterVerifyOTPRequest,
    LoginSendOTPRequest,
    LoginVerifyOTPRequest,
)
from app.email_service import send_otp_email
from app.supabase_auth import (
    send_supabase_email_otp,
    verify_supabase_email_otp,
    validate_email_domain,
)
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY, SESSION_SECRET, AUTH_DEV_MODE, ADMIN_ACCOUNTS, ADMIN_EMAILS

router = APIRouter(prefix="/api/auth", tags=["1. Authentication & Profile Engine"])

LEARNER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@(?:learner\.)?manipal\.edu$", re.IGNORECASE)
REG_NO_PATTERN = re.compile(r"^(\d{9}|\d{12})$")

BRANCH_CODES = {
    # 2-digit branch codes (9-digit registration numbers)
    "01": ("Civil Engineering", "CE"),
    "02": ("Chemical Engineering", "CHE"),
    "03": ("Mechanical Engineering", "ME"),
    "04": ("Mechatronics Engineering", "MTE"),
    "05": ("Computer Science & Engineering", "CSE"),
    "06": ("Aeronautical Engineering", "AE"),
    "07": ("Electronics & Communication Engineering", "ECE"),
    "08": ("Electrical & Electronics Engineering", "EEE"),
    "09": ("Automobile Engineering", "AME"),
    "10": ("Industrial & Production Engineering", "IP"),
    "11": ("Information Technology", "IT"),
    "12": ("Data Science & Engineering", "DSE"),
    "13": ("Computer & Communication Engineering", "CCE"),
    "14": ("Biomedical Engineering", "BME"),
    "15": ("Biotechnology", "BT"),
    "62": ("Computer Science & Engg (AI & ML)", "AIML"),
    # 3-digit branch codes (12-digit registration numbers)
    "001": ("Civil Engineering", "CE"),
    "002": ("Chemical Engineering", "CHE"),
    "003": ("Mechanical Engineering", "ME"),
    "004": ("Mechatronics Engineering", "MTE"),
    "005": ("Computer Science & Engineering", "CSE"),
    "006": ("Aeronautical Engineering", "AE"),
    "007": ("Electronics & Communication Engineering", "ECE"),
    "008": ("Electrical & Electronics Engineering", "EEE"),
    "009": ("Automobile Engineering", "AME"),
    "010": ("Industrial & Production Engineering", "IP"),
    "011": ("Information Technology", "IT"),
    "012": ("Data Science & Engineering", "DSE"),
    "013": ("Computer & Communication Engineering", "CCE"),
    "014": ("Biomedical Engineering", "BME"),
    "015": ("Biotechnology", "BT"),
    "033": ("Aeronautical Engineering", "AE"),
    "062": ("Computer Science & Engg (AI & ML)", "AIML"),
}


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 3:
        masked_local = local[0] + "***"
    else:
        masked_local = local[:2] + "****" + local[-2:]
    return f"{masked_local}@{domain}"


def parse_and_validate_registration_number(reg_no: str) -> dict:
    reg_clean = reg_no.strip()
    if not REG_NO_PATTERN.match(reg_clean):
        raise HTTPException(
            status_code=400,
            detail="Registration Number must be either 9 digits (e.g. 230962088) or 12 digits (e.g. 261090330156).",
        )
    
    year_2d = reg_clean[0:2]
    admission_year = f"20{year_2d}"

    if len(reg_clean) == 9:
        inst_code = reg_clean[2:4]
        branch_code = reg_clean[4:6]
        unique_id = reg_clean[6:9]
        if inst_code != "09":
            raise HTTPException(
                status_code=400,
                detail=f"Institute code '{inst_code}' is invalid. For 9-digit registration numbers, digits 3-4 must be '09' for Manipal campus.",
            )
    else:  # 12 digits
        inst_code = reg_clean[2:5]
        branch_code = reg_clean[5:8]
        unique_id = reg_clean[8:12]
        if inst_code != "109":
            raise HTTPException(
                status_code=400,
                detail=f"Institute code '{inst_code}' is invalid. For 12-digit registration numbers, digits 3-5 must be '109' for Manipal campus.",
            )

    branch_info = BRANCH_CODES.get(branch_code, ("Engineering", "ENGG"))
    dept_name = branch_info[0]

    return {
        "reg_no": reg_clean,
        "format_type": "9_digit" if len(reg_clean) == 9 else "12_digit",
        "admission_year": admission_year,
        "year_2d": year_2d,
        "institute_code": inst_code,
        "branch_code": branch_code,
        "department_name": dept_name,
        "unique_id": unique_id,
    }


# ---------------------------------------------------------------------------
# Session tokens: signed HS256 JWTs, so they survive restarts and serverless cold starts
# ---------------------------------------------------------------------------

if SESSION_SECRET:
    _SESSION_SECRET = SESSION_SECRET
else:
    _SESSION_SECRET = secrets.token_hex(32)
    print("⚠️  SESSION_SECRET not set — using a random per-process secret; sessions end when the server restarts.")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_session_token(user_id: str) -> str:
    # No expiry, for students and admins alike: a session lasts until the user signs out.
    # Signing out (POST /logout or /admin-logout) revokes every token issued before it,
    # and a disabled or removed account is refused on every request.
    now = datetime.datetime.now(datetime.timezone.utc)
    return jwt.encode({"sub": user_id, "iat": now}, _SESSION_SECRET, algorithm="HS256")


def _token_payload(token: Optional[str]) -> Optional[dict]:
    if not token:
        return None
    try:
        return jwt.decode(token, _SESSION_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def resolve_user_id(token: Optional[str]) -> Optional[str]:
    """Returns the user id inside a valid, unexpired session token, else None."""
    if not token:
        return None
    try:
        return jwt.decode(token, _SESSION_SECRET, algorithms=["HS256"]).get("sub")
    except jwt.PyJWTError:
        return None


def token_from_header(authorization: Optional[str]) -> str:
    return (authorization or "").replace("Bearer ", "").strip()


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
    user_id = resolve_user_id(token_from_header(authorization))
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")
    
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="User account not found or disabled.")
        # "Sign out everywhere": reject tokens issued before the account's revocation time.
        g = db.query(models.AdminLoginGuard).filter(models.AdminLoginGuard.email == (user.email or "").lower()).first()
        if g and g.tokens_valid_after:
            iat = (_token_payload(token_from_header(authorization)) or {}).get("iat", 0)
            if datetime.datetime.utcfromtimestamp(iat) < g.tokens_valid_after:
                raise HTTPException(status_code=401, detail="You were signed out. Please sign in again.")
        return user
    finally:
        db.close()


def session_response(user: models.User) -> dict:
    return {
        "access_token": create_session_token(user.id),
        "token_type": "bearer",
        "user": extract_user_dict(user),
    }


# ---------------------------------------------------------------------------
# OTP issue / verify — shared by every signup and sign-in endpoint
# ---------------------------------------------------------------------------

OTP_TTL = datetime.timedelta(minutes=10)
OTP_RESEND_COOLDOWN = datetime.timedelta(seconds=45)
OTP_MAX_ATTEMPTS = 5
# otp_hash markers: Supabase owns the code itself, so there's no local hash to store
SUPABASE_OTP_MARKER = "supabase-managed"
# Marks a code as already verified, so it can't be reused
VERIFIED_OTP_PREFIX = "verified:"


def supabase_enabled() -> bool:
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY)


def _hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _latest_otp(db, lid: str) -> Optional[models.OTPRecord]:
    return (
        db.query(models.OTPRecord)
        .filter(models.OTPRecord.learner_id == lid)
        .order_by(models.OTPRecord.id.desc())
        .first()
    )


def _issue_otp(db, lid: str, purpose: str = "signup", name: str = "") -> dict:
    """Enforces the resend cooldown, sends a fresh 6-digit code to the Learner ID mailbox,
    and records it. `purpose`/`name` only shape the email. Returns {"dev_mode", "test_otp"}."""
    now = datetime.datetime.utcnow()
    last_otp = _latest_otp(db, lid)
    if last_otp and last_otp.resend_cooldown_until and now < last_otp.resend_cooldown_until:
        wait_seconds = int((last_otp.resend_cooldown_until - now).total_seconds()) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {wait_seconds} seconds before requesting another OTP.",
        )

    raw_otp = None
    if supabase_enabled():
        # Send first: if Supabase refuses, no cooldown is recorded and the student can retry
        send_supabase_email_otp(lid)
        otp_hash = SUPABASE_OTP_MARKER
    else:
        raw_otp = f"{secrets.randbelow(1_000_000):06d}"
        send_result = send_otp_email(lid, raw_otp, purpose=purpose, name=name)
        if not send_result.get("delivered"):
            raise HTTPException(status_code=502, detail="Could not send the verification email. Please try again shortly.")
        otp_hash = _hash_otp(raw_otp)

    # Invalidate previous unused codes, then store the new one
    db.query(models.OTPRecord).filter(
        models.OTPRecord.learner_id == lid,
        models.OTPRecord.is_used == False,
    ).update({"is_used": True})
    db.add(models.OTPRecord(
        learner_id=lid,
        otp_hash=otp_hash,
        attempts=0,
        is_used=False,
        expires_at=now + OTP_TTL,
        resend_cooldown_until=now + OTP_RESEND_COOLDOWN,
    ))
    db.commit()

    dev_mode = raw_otp is not None and AUTH_DEV_MODE
    return {"dev_mode": dev_mode, "test_otp": raw_otp if dev_mode else None}


def _verify_otp(db, lid: str, otp_code: str) -> None:
    """Checks a code against the latest one issued to `lid` and marks it used.
    Raises HTTPException(400) with a student-facing message on any failure."""
    otp_code = (otp_code or "").strip()
    if not re.fullmatch(r"\d{6}", otp_code):
        raise HTTPException(status_code=400, detail="Invalid OTP format. OTP must be a 6-digit numeric code.")

    otp_rec = _latest_otp(db, lid)
    if not otp_rec:
        raise HTTPException(status_code=400, detail="No active OTP request found. Please request an OTP first.")
    if otp_rec.is_used:
        raise HTTPException(status_code=400, detail="This OTP code has already been used. Please request a new code.")
    if datetime.datetime.utcnow() > otp_rec.expires_at:
        raise HTTPException(status_code=400, detail="OTP code has expired. Please request a new code.")
    if otp_rec.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=400, detail="Maximum OTP verification attempts exceeded. Please request a new code.")

    failure = None
    if otp_rec.otp_hash == SUPABASE_OTP_MARKER:
        try:
            verify_supabase_email_otp(lid, otp_code)
        except HTTPException as e:
            if e.status_code != 400:
                raise  # Supabase unreachable / misconfigured — not the student's fault, don't burn an attempt
            failure = e.detail
    elif not hmac.compare_digest(otp_rec.otp_hash, _hash_otp(otp_code)):
        failure = "Incorrect OTP code."

    if failure:
        otp_rec.attempts += 1
        db.commit()
        remaining = OTP_MAX_ATTEMPTS - otp_rec.attempts
        if remaining <= 0:
            raise HTTPException(status_code=400, detail=f"{failure} Maximum attempts reached — please request a new code.")
        raise HTTPException(status_code=400, detail=f"{failure} {remaining} attempt(s) remaining.")

    otp_rec.is_used = True
    otp_rec.otp_hash = VERIFIED_OTP_PREFIX + _hash_otp(otp_code)
    db.commit()


def _validate_registration_details(name: str, reg_no: str, lid: str) -> dict:
    """Validates signup fields and that the reg-no admission year matches the Learner ID."""
    if not name or len(name) < 2:
        raise HTTPException(status_code=400, detail="Please enter your full name.")

    parsed_reg = parse_and_validate_registration_number(reg_no)

    if not validate_email_domain(lid):
        raise HTTPException(
            status_code=400,
            detail="Invalid student email domain. Must be an official @learner.manipal.edu address.",
        )

    year_match = re.search(r"20[0-9]{2}", lid)
    if year_match and year_match.group(0)[-2:] != parsed_reg["year_2d"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Admission year mismatch: Registration number begins with '{parsed_reg['year_2d']}' "
                f"({parsed_reg['admission_year']}), but Learner ID specifies year '{year_match.group(0)}'."
            ),
        )
    return parsed_reg


def _ensure_not_registered(db, reg_no: Optional[str], lid: str) -> None:
    if reg_no and db.query(models.User).filter(models.User.registration_number == reg_no).first():
        raise HTTPException(
            status_code=400,
            detail=f"Registration Number {reg_no} is already registered. Please sign in instead.",
        )
    if db.query(models.User).filter(models.User.learner_id == lid).first():
        raise HTTPException(
            status_code=400,
            detail=f"Learner ID {lid} is already registered. Please sign in instead.",
        )


def _find_user_by_identifier(db, ident: str) -> Optional[models.User]:
    # Admin accounts can only sign in through /admin-send-otp (allowlist, lockout, short
    # sessions, never a dev-mode code), so the student flows don't see them.
    return (
        db.query(models.User)
        .filter(
            (models.User.email == ident)
            | (models.User.learner_id == ident)
            | (models.User.registration_number == ident)
        )
        .filter(models.User.role != "admin")
        .first()
    )


# ---------------------------------------------------------------------------
# Primary flow (AuthPage): register with Name + Reg No + Learner ID, sign in with either ID
# ---------------------------------------------------------------------------

@router.post("/register-send-otp", summary="Validate Name, Reg No & Learner ID and email a signup OTP")
def register_send_otp(req: RegisterSendOTPRequest):
    name = req.name.strip()
    lid = req.learner_id.strip().lower()
    reg_no = req.registration_number.strip()

    parsed_reg = _validate_registration_details(name, reg_no, lid)

    db = SessionLocal()
    try:
        _ensure_not_registered(db, reg_no, lid)
        g = _count_code_sent(db, lid, STUDENT_MAX_CODES_PER_DAY)
        otp = _issue_otp(db, lid, purpose="signup", name=name)
        g.codes_sent = (g.codes_sent or 0) + 1
        db.commit()
        return {
            "status": "success",
            "message": f"Verification OTP sent to {lid}.",
            "learner_id": lid,
            "registration_number": reg_no,
            "parsed_info": parsed_reg,
            "dev_mode": otp["dev_mode"],
            "test_otp": otp["test_otp"],
            "expires_in_seconds": int(OTP_TTL.total_seconds()),
        }
    finally:
        db.close()


@router.post("/register-verify-otp", summary="Verify signup OTP and create the student account")
def register_verify_otp(req: RegisterVerifyOTPRequest):
    name = req.name.strip()
    lid = req.learner_id.strip().lower()
    reg_no = req.registration_number.strip()

    parsed_reg = _validate_registration_details(name, reg_no, lid)

    db = SessionLocal()
    try:
        _ensure_not_registered(db, reg_no, lid)
        _verify_guarded(db, lid, req.otp_code)

        new_user = models.User(
            id=f"usr_std_{secrets.token_hex(6)}",
            email=lid,
            learner_id=lid,
            registration_number=reg_no,
            admission_year=parsed_reg["admission_year"],
            password_hash=hash_password(secrets.token_hex(16)),  # OTP-only account, no usable password
            name=name,
            role="student",
            is_verified=True,
            account_state="Verified",
            department=parsed_reg["department_name"],
            academic_year=f"{parsed_reg['admission_year']} Batch",
            semester="Even Semester (Jan - May)",
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
        return session_response(new_user)
    finally:
        db.close()


@router.post("/login-send-otp", summary="Email a sign-in OTP to the student's registered Learner ID")
def login_send_otp(req: LoginSendOTPRequest):
    ident = req.identifier.strip().lower()
    if not ident:
        raise HTTPException(status_code=400, detail="Please enter your Learner ID or 9-digit Registration Number.")

    db = SessionLocal()
    try:
        user = _find_user_by_identifier(db, ident)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="No account found matching this Learner ID or Registration Number. Please create an account first.",
            )
        # Suspended students can still sign in (read-only, with a plea); disabled accounts can't.
        if user.status != "active":
            raise HTTPException(status_code=403, detail="This account has been disabled.")

        lid = (user.learner_id or user.email).lower()
        g = _count_code_sent(db, lid, STUDENT_MAX_CODES_PER_DAY)
        otp = _issue_otp(db, lid, purpose="signin", name=user.name)
        g.codes_sent = (g.codes_sent or 0) + 1
        db.commit()
        masked = mask_email(lid)
        return {
            "status": "success",
            "message": f"Verification code sent to {masked}",
            "learner_id": lid,
            "masked_email": masked,
            "dev_mode": otp["dev_mode"],
            "test_otp": otp["test_otp"],
            "expires_in_seconds": int(OTP_TTL.total_seconds()),
        }
    finally:
        db.close()


@router.post("/login-verify-otp", summary="Verify sign-in OTP and start a session")
def login_verify_otp(req: LoginVerifyOTPRequest):
    ident = req.identifier.strip().lower()
    if not ident:
        raise HTTPException(status_code=400, detail="Identifier is required.")

    db = SessionLocal()
    try:
        user = _find_user_by_identifier(db, ident)
        if not user:
            raise HTTPException(status_code=404, detail="User account not found.")
        # Suspended students can still sign in (read-only, with a plea); disabled accounts can't.
        if user.status != "active":
            raise HTTPException(status_code=403, detail="This account has been disabled.")

        _verify_guarded(db, (user.learner_id or user.email).lower(), req.otp_code)
        return session_response(user)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Admin sign-in: the hard-coded admins only (config.ADMIN_ACCOUNTS), same OTP rules as students.
# Admin accounts are separate from student accounts and named by their owner.
# ---------------------------------------------------------------------------

class AdminSendOTPRequest(BaseModel):
    email: str


class AdminVerifyOTPRequest(BaseModel):
    email: str
    otp_code: str


# Sign-in throttling, shared by student and admin sign-in (AdminLoginGuard is keyed by email
# for any account): wrong codes count across codes, so requesting fresh codes can't reset it.
ADMIN_MAX_FAILED = 5  # wrong codes, across any number of codes, before locking
ADMIN_FAIL_WINDOW = datetime.timedelta(minutes=30)
ADMIN_LOCKOUT = datetime.timedelta(minutes=30)
ADMIN_MAX_CODES_PER_DAY = 10
STUDENT_MAX_CODES_PER_DAY = 20


def _guard(db, email: str) -> models.AdminLoginGuard:
    g = db.query(models.AdminLoginGuard).filter(models.AdminLoginGuard.email == email).first()
    if not g:
        g = models.AdminLoginGuard(email=email, failed_attempts=0, codes_sent=0)
        db.add(g)
        db.flush()
    return g


def _check_not_locked(g: models.AdminLoginGuard) -> None:
    now = datetime.datetime.utcnow()
    if g.locked_until and now < g.locked_until:
        mins = int((g.locked_until - now).total_seconds() // 60) + 1
        raise HTTPException(status_code=429, detail=f"Too many wrong codes. Admin sign-in is locked for {mins} more minute(s).")


def _record_failure(db, g: models.AdminLoginGuard) -> None:
    now = datetime.datetime.utcnow()
    if not g.window_started_at or now - g.window_started_at > ADMIN_FAIL_WINDOW:
        g.window_started_at, g.failed_attempts = now, 0
    g.failed_attempts = (g.failed_attempts or 0) + 1
    if g.failed_attempts >= ADMIN_MAX_FAILED:
        g.locked_until, g.failed_attempts, g.window_started_at = now + ADMIN_LOCKOUT, 0, None
    db.commit()


def _count_code_sent(db, email: str, cap: int) -> models.AdminLoginGuard:
    """Applies the lockout and the daily code cap before a code is emailed."""
    g = _guard(db, email)
    _check_not_locked(g)
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    if g.codes_day != today:
        g.codes_day, g.codes_sent = today, 0
    if (g.codes_sent or 0) >= cap:
        raise HTTPException(status_code=429, detail="Daily limit for sign-in codes reached. Try again tomorrow.")
    return g


def _verify_guarded(db, email: str, otp_code: str) -> None:
    """_verify_otp plus the cross-code lockout: 5 wrong codes lock sign-in for 30 minutes."""
    g = _guard(db, email)
    db.commit()
    _check_not_locked(g)
    try:
        _verify_otp(db, email, otp_code)
    except HTTPException as e:
        if e.status_code == 400:
            _record_failure(db, g)
            if g.locked_until:
                raise HTTPException(status_code=429, detail="Too many wrong codes. Sign-in is locked for 30 minutes.")
        raise
    g.failed_attempts, g.window_started_at = 0, None
    db.commit()


def _require_allowlisted(email: str) -> str:
    email = (email or "").strip().lower()
    # Same message whether or not the email exists, so the allowlist can't be probed.
    if email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="This email isn't authorised for admin access.")
    return email


@router.post("/admin-send-otp", summary="Email a sign-in OTP to an allowlisted admin email")
def admin_send_otp(req: AdminSendOTPRequest):
    email = _require_allowlisted(req.email)
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        if user and user.role != "admin":
            raise HTTPException(status_code=409, detail="This email belongs to a student account and can't be used for admin access.")
        if user and user.status != "active":
            raise HTTPException(status_code=403, detail="This admin account is disabled.")
        g = _count_code_sent(db, email, ADMIN_MAX_CODES_PER_DAY)
        _issue_otp(db, email, purpose="signin", name=(user.name if user else ""))
        g.codes_sent = (g.codes_sent or 0) + 1
        db.commit()
        # Never echo the code here, even with AUTH_DEV_MODE: knowing an admin email
        # must never be enough to sign in. (Without email configured it's only printed
        # to the backend console.)
        return {
            "status": "success",
            "message": f"Verification code sent to {mask_email(email)}",
            "learner_id": email,
            "masked_email": mask_email(email),
            "dev_mode": False,
            "test_otp": None,
            "expires_in_seconds": int(OTP_TTL.total_seconds()),
        }
    finally:
        db.close()


@router.post("/admin-verify-otp", summary="Verify an admin OTP; creates the admin account on first sign-in")
def admin_verify_otp(req: AdminVerifyOTPRequest):
    email = _require_allowlisted(req.email)
    db = SessionLocal()
    try:
        _verify_guarded(db, email, req.otp_code)
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            user = models.User(
                id=f"usr_adm_{secrets.token_hex(6)}",
                email=email,
                password_hash=hash_password(secrets.token_hex(16)),  # OTP-only account
                name=ADMIN_ACCOUNTS[email],
                role="admin",
                is_verified=True,
                account_state="Verified",
                agreed_terms=True,
                status="active",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        elif user.role != "admin":
            raise HTTPException(status_code=409, detail="This email belongs to a student account.")
        elif user.name != ADMIN_ACCOUNTS[email]:
            user.name = ADMIN_ACCOUNTS[email]  # names are fixed in config, not chosen
            db.commit()
            db.refresh(user)
        return session_response(user)
    finally:
        db.close()


def get_current_admin(authorization: Optional[str] = Header(None)) -> models.User:
    user = get_current_user(authorization)
    # Only the hard-coded admins: an account not in ADMIN_ACCOUNTS is refused even with a live token.
    if user.role != "admin" or (user.email or "").lower() not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Access denied: admin privileges required.")
    return user


@router.post("/logout", summary="Sign out on every device (revokes all of this account's tokens)")
def logout(me: models.User = Depends(get_current_user)):
    return _revoke_all(me)


@router.post("/admin-logout", summary="Sign this admin out on every device (revokes all their tokens)")
def admin_logout(admin: models.User = Depends(get_current_admin)):
    return _revoke_all(admin)


def _revoke_all(user: models.User) -> dict:
    db = SessionLocal()
    try:
        g = _guard(db, (user.email or "").lower())
        # iat has 1-second resolution, so revoke everything issued up to the end of this second.
        g.tokens_valid_after = datetime.datetime.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=1)
        db.commit()
        return {"status": "signed_out"}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Appeals for disabled accounts: they can't sign in, so they prove the learner email
# with a one-time code (same lockout and daily cap as sign-in) and appeal from here.
# ---------------------------------------------------------------------------

class AppealCodeRequest(BaseModel):
    identifier: str


class AppealSubmitRequest(BaseModel):
    identifier: str
    otp_code: str
    text: str = ""  # empty: only check the status of an existing appeal


def _disabled_student(db, ident: str) -> models.User:
    user = _find_user_by_identifier(db, (ident or "").strip().lower())
    if not user:
        raise HTTPException(status_code=404, detail="No account found matching this Learner ID or Registration Number.")
    if user.status == "active":
        raise HTTPException(status_code=400, detail="This account isn't disabled. You can sign in normally.")
    return user


def _appeal_dict(a: Optional[models.AccountAppeal]) -> Optional[dict]:
    if not a:
        return None
    return {"status": a.status, "text": a.text, "decision_note": a.decision_note, "sent_at": a.created_at.isoformat() + "Z" if a.created_at else None}


@router.post("/appeal-send-otp", summary="Email a code so a disabled student can appeal")
def appeal_send_otp(req: AppealCodeRequest):
    db = SessionLocal()
    try:
        user = _disabled_student(db, req.identifier)
        lid = (user.learner_id or user.email).lower()
        g = _count_code_sent(db, lid, STUDENT_MAX_CODES_PER_DAY)
        _issue_otp(db, lid, purpose="signin", name=user.name)
        g.codes_sent = (g.codes_sent or 0) + 1
        db.commit()
        return {"status": "success", "masked_email": mask_email(lid), "expires_in_seconds": int(OTP_TTL.total_seconds())}
    finally:
        db.close()


@router.post("/appeal", summary="Verify the code, then submit an appeal (or read the latest one's status)")
def appeal_submit(req: AppealSubmitRequest):
    text = (req.text or "").strip()
    if text and len(text) < 20:
        raise HTTPException(status_code=400, detail="Please explain your side in at least 20 characters.")
    if len(text) > 2000:
        raise HTTPException(status_code=400, detail="Please keep your appeal under 2000 characters.")
    db = SessionLocal()
    try:
        user = _disabled_student(db, req.identifier)
        _verify_guarded(db, (user.learner_id or user.email).lower(), req.otp_code)
        latest = (
            db.query(models.AccountAppeal)
            .filter(models.AccountAppeal.user_id == user.id)
            .order_by(models.AccountAppeal.id.desc())
            .first()
        )
        if not text:
            return {"status": "checked", "appeal": _appeal_dict(latest)}
        if latest and latest.status == "pending":
            raise HTTPException(status_code=409, detail="Your appeal is already with the MITra team. You'll be able to sign in once it's accepted.")
        appeal = models.AccountAppeal(user_id=user.id, text=text)
        db.add(appeal)
        db.commit()
        db.refresh(appeal)
        # Show a previously rejected appeal's note alongside the new one.
        return {"status": "submitted", "appeal": _appeal_dict(appeal), "previous": _appeal_dict(latest)}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@router.get("/me", summary="Fetch current authenticated user profile")
def get_me(me: models.User = Depends(get_current_user)):
    # Shared check: rejects expired, revoked (signed out) and disabled sessions.
    return extract_user_dict(me)


@router.put("/profile", summary="Update permitted profile fields (department, academic year, bio, etc.)")
def update_profile(req: ProfileUpdateRequest, me: models.User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == me.id).first()
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
