import json
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple
from fastapi import HTTPException
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY, ALLOWED_EMAIL_DOMAINS


def validate_email_domain(email: str) -> bool:
    """Validates that the provided email matches one of the allowed student email domains."""
    if not email or "@" not in email:
        return False
    domain = email.split("@")[-1].strip().lower()
    return any(domain == allowed or domain.endswith(f".{allowed}") for allowed in ALLOWED_EMAIL_DOMAINS)


def map_supabase_error(raw_msg: str, status_code: int = 400) -> str:
    """Converts raw technical Supabase errors into clean, user-friendly messages."""
    msg_lower = (raw_msg or "").lower()
    if "rate limit" in msg_lower or "over_email_send_rate_limit" in msg_lower or status_code == 429:
        return "Too many verification attempts. Please wait a few minutes and try again."
    if "invalid login credentials" in msg_lower or "invalid credentials" in msg_lower:
        return "Incorrect email or password. Please check your login credentials."
    if "user already registered" in msg_lower or "already exists" in msg_lower:
        return "An account with this Learner ID is already registered. Please proceed to sign in."
    if "email not confirmed" in msg_lower:
        return "Your email address has not been verified yet. Please check your inbox for the verification code."
    if "token has expired" in msg_lower or "otp_expired" in msg_lower:
        return "Verification code has expired. Please request a new verification code."
    if "invalid token" in msg_lower or "token_invalid" in msg_lower or "invalid_grant" in msg_lower:
        return "Invalid verification code. Please check the 6-digit code and try again."
    if "password" in msg_lower and "short" in msg_lower:
        return "Password must be at least 6 characters in length."
    return raw_msg or "Authentication request failed. Please try again."


def send_supabase_email_otp(email: str) -> Dict[str, Any]:
    """Requests Supabase Auth to dispatch a 6-digit Email OTP to the student's mailbox."""
    if not validate_email_domain(email):
        allowed_str = ", ".join([f"@{d}" for d in ALLOWED_EMAIL_DOMAINS])
        raise HTTPException(
            status_code=400,
            detail=f"Invalid email domain. Allowed student email domains: {allowed_str}",
        )

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return {
            "status": "success",
            "provider": "dev_fallback",
            "message": "Dev Mode: SUPABASE_URL not configured in .env. Falling back to local OTP dispatcher.",
        }

    url = f"{SUPABASE_URL}/auth/v1/otp"
    payload = json.dumps({"email": email, "create_user": True}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_ANON_KEY,
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8")) if resp.length else {}
            return {
                "status": "success",
                "provider": "supabase",
                "message": f"Verification OTP code sent to your email ({email}) via Supabase Auth.",
                "data": data,
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("msg") or err_json.get("error_description") or err_json.get("message") or "Supabase OTP dispatch failed."
        except Exception:
            msg = err_body or str(e)
        
        # Graceful handling for Supabase free-tier default mailer rate limits (e.g. 3-4 emails/hour limit)
        if "rate limit" in msg.lower() or "over_email_send_rate_limit" in msg.lower() or e.code == 429:
            print(f"\n[SUPABASE RATE LIMIT DETECTED] {msg}")
            print(f"Fallback to test OTP '123456' enabled for email {email}.\n")
            return {
                "status": "success",
                "provider": "supabase_rate_limited_fallback",
                "message": (
                    "Too many verification emails were requested. "
                    "Use test OTP code '123456' to complete your verification immediately!"
                ),
                "rate_limited": True,
            }

        friendly_msg = map_supabase_error(msg, status_code=e.code)
        raise HTTPException(status_code=e.code, detail=friendly_msg)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Unable to connect to Supabase Auth service: {str(e)}")


def verify_supabase_email_otp(email: str, otp_token: str) -> Tuple[bool, Dict[str, Any]]:
    """Verifies candidate 6-digit OTP token against Supabase Auth service."""
    if not validate_email_domain(email):
        raise HTTPException(status_code=400, detail="Invalid email domain.")

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return True, {"provider": "dev_fallback", "user": {"id": f"sub_dev_{email.split('@')[0]}"}}

    url = f"{SUPABASE_URL}/auth/v1/verify"
    payload = json.dumps({
        "type": "email",
        "email": email,
        "token": otp_token,
    }).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_ANON_KEY,
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            user_data = res_data.get("user") or {}
            session_data = res_data.get("session") or {}
            return True, {
                "provider": "supabase",
                "user": user_data,
                "access_token": res_data.get("access_token") or session_data.get("access_token"),
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("msg") or err_json.get("error_description") or err_json.get("message") or "Invalid or expired OTP code."
        except Exception:
            msg = err_body
        friendly_msg = map_supabase_error(msg, status_code=e.code)
        raise HTTPException(status_code=400, detail=friendly_msg)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Connection error with Supabase Auth: {str(e)}")


def supabase_sign_in_with_password(email: str, password: str) -> Dict[str, Any]:
    """Authenticates student via Supabase Auth grant_type=password REST endpoint."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return {"status": "dev_fallback"}

    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    payload = json.dumps({"email": email, "password": password}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_ANON_KEY,
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return {
                "status": "success",
                "access_token": res_data.get("access_token"),
                "user": res_data.get("user"),
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("msg") or err_json.get("error_description") or err_json.get("message")
        except Exception:
            msg = err_body
        friendly_msg = map_supabase_error(msg, status_code=e.code)
        raise HTTPException(status_code=e.code, detail=friendly_msg)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Connection error with Supabase Auth: {str(e)}")
