"""
OTP email templates (HTML + plain-text fallback).

Built with tables and inline styles, since Outlook/Gmail strip <style> blocks and
modern CSS. The MITra logo is drawn in HTML (not an image) so it still shows when the
mail client blocks remote images — Outlook, which @learner.manipal.edu uses, does by default.
Brand colours match frontend/src/components/Logo.jsx.
"""
from html import escape

TEAL = "#234f4a"
LIME = "#d8ef68"
CORAL = "#e07b64"
CREAM = "#f9faf5"
PAGE_BG = "#eef1e8"
MUTED = "#5f6f6c"
FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

PURPOSES = {
    "signup": {
        "subject": "{code} is your MITra verification code",
        "heading": "Verify your Learner ID",
        "intro": "Welcome to MITra! Enter this code to finish creating your account.",
    },
    "signin": {
        "subject": "{code} is your MITra sign-in code",
        "heading": "Your sign-in code",
        "intro": "Enter this code to sign in to MITra.",
    },
}


def _logo_html() -> str:
    # Light variant of Logo.jsx: lime "M" badge + "MIT" in cream + "ra" in coral
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td width="36" height="36" align="center" valign="middle"
        style="width:36px;height:36px;background:{LIME};color:{TEAL};border-radius:9px 4px 9px 4px;
               font-family:{FONT};font-size:20px;font-weight:800;letter-spacing:-1px;line-height:36px;">M</td>
    <td style="padding-left:11px;font-family:{FONT};font-size:28px;font-weight:800;letter-spacing:-2px;
               color:{CREAM};line-height:36px;">MIT<span style="color:{CORAL};">ra</span></td>
  </tr>
</table>"""


def render_otp_email(code: str, to_email: str, purpose: str = "signup", name: str = "",
                     expires_minutes: int = 10) -> tuple[str, str, str]:
    """Returns (subject, plain_text, html) for an OTP email."""
    p = PURPOSES.get(purpose, PURPOSES["signup"])
    subject = p["subject"].format(code=code)
    first_name = (name or "").strip().split(" ")[0]
    greeting = f"Hi {first_name}," if first_name else "Hi there,"

    text = (
        f"{greeting}\n\n"
        f"{p['intro']}\n\n"
        f"Your code: {code}\n\n"
        f"It expires in {expires_minutes} minutes and can only be used once.\n\n"
        f"Didn't request this? You can safely ignore this email - nobody can sign in without the code. "
        f"MITra will never ask you to share it.\n\n"
        f"- MITra, the MIT Manipal campus assistant\n"
        f"Sent to {to_email}"
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background:{PAGE_BG};">
<!-- Inbox preview text -->
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:{PAGE_BG};">
  Your MITra code is {code}. It expires in {expires_minutes} minutes.&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;
</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{PAGE_BG};">
  <tr>
    <td align="center" style="padding:32px 16px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
             style="max-width:520px;background:#ffffff;border-radius:18px;overflow:hidden;">
        <!-- Header -->
        <tr>
          <td style="background:{TEAL};padding:26px 32px;">{_logo_html()}</td>
        </tr>
        <!-- Lime accent line -->
        <tr><td style="background:{LIME};height:4px;line-height:4px;font-size:0;">&nbsp;</td></tr>
        <!-- Body -->
        <tr>
          <td style="padding:34px 32px 8px 32px;font-family:{FONT};color:{TEAL};">
            <p style="margin:0 0 6px 0;font-size:15px;color:{MUTED};">{escape(greeting)}</p>
            <h1 style="margin:0 0 12px 0;font-size:24px;line-height:1.25;font-weight:800;letter-spacing:-0.5px;color:{TEAL};">{p['heading']}</h1>
            <p style="margin:0;font-size:15px;line-height:1.6;color:#3d4f4c;">{p['intro']}</p>
          </td>
        </tr>
        <!-- Code -->
        <tr>
          <td align="center" style="padding:24px 32px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td align="center"
                    style="background:#f4f9de;border:2px solid {LIME};border-radius:14px;padding:20px 12px;
                           font-family:'SF Mono',Menlo,Consolas,'Courier New',monospace;font-size:38px;
                           font-weight:700;letter-spacing:12px;color:{TEAL};">{code}</td>
              </tr>
            </table>
            <p style="margin:14px 0 0 0;font-family:{FONT};font-size:13px;color:{MUTED};">
              Expires in <strong style="color:{TEAL};">{expires_minutes} minutes</strong> &middot; single use
            </p>
          </td>
        </tr>
        <!-- Security note -->
        <tr>
          <td style="padding:8px 32px 30px 32px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="border-left:3px solid {CORAL};background:#fbf3f0;border-radius:4px;padding:12px 16px;
                           font-family:{FONT};font-size:13px;line-height:1.55;color:#5c4741;">
                  <strong>Didn't request this?</strong> You can safely ignore this email &mdash; nobody can sign in
                  without the code. MITra will never ask you to share it.
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="background:{CREAM};border-top:1px solid #e3e8dc;padding:18px 32px;font-family:{FONT};
                     font-size:12px;line-height:1.6;color:{MUTED};">
            <strong style="color:{TEAL};">MITra</strong> &middot; the MIT Manipal campus assistant<br>
            Sent to {escape(to_email)} because a code was requested for this Learner ID.
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""
    return subject, text, html
