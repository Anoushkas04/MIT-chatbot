import os
import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from app.config import AUTH_DEV_MODE
from app.email_templates import render_otp_email

logger = logging.getLogger("email_service")


def get_smtp_config():
    return {
        "host": os.environ.get("SMTP_HOST", "").strip(),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", "").strip(),
        "password": os.environ.get("SMTP_PASSWORD", "").strip(),
        "from_email": os.environ.get("SMTP_FROM", os.environ.get("SMTP_USER", "")).strip() or "noreply@manipal.edu",
        "from_name": os.environ.get("SMTP_FROM_NAME", "MITra").strip(),
    }


def is_smtp_configured() -> bool:
    config = get_smtp_config()
    return bool(config["host"] and config["user"] and config["password"])


def send_otp_email(to_email: str, otp_code: str, purpose: str = "signup", name: str = "") -> dict:
    """
    Attempts to send a 6-digit OTP code to the student's @learner.manipal.edu mailbox via SMTP.
    `purpose` ("signup" | "signin") picks the email wording; `name` personalises the greeting.
    If SMTP credentials are missing, returns an explicit unconfigured status.
    If SMTP dispatch fails, catches the exact exception, logs it, and returns the provider error.
    """
    config = get_smtp_config()

    if not is_smtp_configured() and not AUTH_DEV_MODE:
        # A deployed server with no email provider must fail loudly: reporting the code as
        # sent while it only went to the console leaves students waiting for an email
        # that never comes.
        logger.error(
            f"No email provider configured — cannot send OTP to {to_email}. Set SUPABASE_URL + "
            f"SUPABASE_ANON_KEY or SMTP_HOST/SMTP_USER/SMTP_PASSWORD (or AUTH_DEV_MODE=true locally)."
        )
        return {
            "delivered": False,
            "error_type": "EMAIL_NOT_CONFIGURED",
            "message": "No email provider is configured on the server.",
        }

    if not is_smtp_configured():
        # Local-development fallback (AUTH_DEV_MODE): no SMTP provider configured, so log
        # the OTP to the console instead of blocking sign-up entirely.
        logger.warning(f"SMTP not configured — logging OTP for {to_email} to console (dev mode).")
        print(f"\n=======================================================")
        print(f"[DEV MODE — SMTP NOT CONFIGURED]")
        print(f"OTP for {to_email}: {otp_code}")
        print(f"Configure SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD in backend/.env to send real emails.")
        print(f"=======================================================\n")
        return {
            "delivered": True,
            "method": "console",
            "message": "SMTP not configured — OTP was logged to the backend console for local development.",
        }

    subject, text_body, html_body = render_otp_email(otp_code, to_email, purpose=purpose, name=name)

    try:
        # Plain text first, HTML last: clients show the last part they can render
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((config["from_name"], config["from_email"]))
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        logger.info(f"Connecting to SMTP server {config['host']}:{config['port']}...")
        with smtplib.SMTP(config["host"], config["port"], timeout=12) as server:
            server.starttls()
            server.login(config["user"], config["password"])
            server.send_message(msg)

        logger.info(f"✓ Real OTP email successfully delivered to {to_email} via SMTP server {config['host']}")
        return {"delivered": True, "method": "smtp", "host": config["host"]}
    except Exception as e:
        err_msg = str(e)
        stack = traceback.format_exc()
        logger.error(f"❌ SMTP Provider Error delivering to {to_email}:\n{stack}")
        print(f"\n=======================================================")
        print(f"[SMTP PROVIDER DISPATCH FAILURE]")
        print(f"Recipient: {to_email}")
        print(f"Error: {err_msg}")
        print(f"Traceback:\n{stack}")
        print(f"=======================================================\n")
        return {
            "delivered": False,
            "error_type": "SMTP_PROVIDER_ERROR",
            "message": f"SMTP Provider Error: {err_msg}",
            "detail": err_msg,
        }
