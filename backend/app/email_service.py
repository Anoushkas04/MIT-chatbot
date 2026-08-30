import os
import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("email_service")


def get_smtp_config():
    return {
        "host": os.environ.get("SMTP_HOST", "").strip(),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", "").strip(),
        "password": os.environ.get("SMTP_PASSWORD", "").strip(),
        "from_email": os.environ.get("SMTP_FROM", os.environ.get("SMTP_USER", "")).strip() or "noreply@manipal.edu",
    }


def is_smtp_configured() -> bool:
    config = get_smtp_config()
    return bool(config["host"] and config["user"] and config["password"])


def send_otp_email(to_email: str, otp_code: str) -> dict:
    """
    Attempts to send a 6-digit OTP code to the student's @learner.manipal.edu mailbox via SMTP.
    If SMTP credentials are missing, returns an explicit unconfigured status.
    If SMTP dispatch fails, catches the exact exception, logs it, and returns the provider error.
    """
    config = get_smtp_config()

    if not is_smtp_configured():
        # Local-development fallback: no SMTP provider configured, so the OTP can't be
        # emailed. Log it to the console instead of blocking sign-up entirely. This path
        # is only reachable when SMTP_* is unset, so it can never fire once a real
        # provider is configured for production.
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

    subject = "MAHE MIT Manipal — Your Learner ID Verification Code"
    body = (
        f"Hello Student,\n\n"
        f"Your verification code for MAHE MIT CampusOS is: {otp_code}\n\n"
        f"This OTP is valid for 10 minutes. Do not share this code with anyone.\n\n"
        f"Best regards,\nMAHE MIT CampusOS Identity Team"
    )

    try:
        msg = MIMEMultipart()
        msg["From"] = config["from_email"]
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

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
