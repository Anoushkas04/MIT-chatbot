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


def send_supabase_email_otp(email: str) -> Dict[str, Any]:
    """Requests Supabase Auth to dispatch a 6-digit Email OTP to the student's mailbox."""
    if not validate_email_domain(email):
        allowed_str = ", ".join([f"@{d}" for d in ALLOWED_EMAIL_DOMAINS])
        raise HTTPException(
            status_code=400,
            detail=f"Invalid email domain. Allowed student email domains: {allowed_str}",
        )

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        # Fallback for dev mode before Supabase credentials are put in .env
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
        raise HTTPException(status_code=e.code, detail=f"Supabase Auth Error: {msg}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Unable to connect to Supabase Auth service: {str(e)}")


def verify_supabase_email_otp(email: str, otp_token: str) -> Tuple[bool, Dict[str, Any]]:
    """Verifies candidate 6-digit OTP token against Supabase Auth service."""
    if not validate_email_domain(email):
        raise HTTPException(status_code=400, detail="Invalid email domain.")

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        # Dev fallback mode
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
            msg = "Invalid or expired OTP code."
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Connection error with Supabase Auth: {str(e)}")
