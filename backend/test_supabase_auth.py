"""
End-to-end check of Learner ID OTP signup / sign-in against a running backend.

Needs the server started in local dev mode (no Supabase, OTP returned as test_otp)
and a throwaway database, e.g.:

    DATABASE_URL=sqlite:////tmp/authtest.db AUTH_DEV_MODE=true SESSION_SECRET=test \
    SUPABASE_URL= SUPABASE_ANON_KEY= uvicorn app.main:app --port 8001

    python test_supabase_auth.py http://127.0.0.1:8001 main /tmp/token.txt
    # restart the server with the same SESSION_SECRET, then:
    python test_supabase_auth.py http://127.0.0.1:8001 restart /tmp/token.txt

Takes ~2 minutes (it waits out the 45s resend cooldown twice).
"""
import sys
import time
import requests

B = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
A = f"{B}/api/auth"
results = []


def check(name, cond, extra=""):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))


for _ in range(40):
    try:
        requests.get(f"{B}/api/health", timeout=1)
        break
    except Exception:
        time.sleep(0.5)

phase = sys.argv[2] if len(sys.argv) > 2 else "main"

if phase == "main":
    lid = "test.mitmpl2023@learner.manipal.edu"
    reg = "230905123"
    body = {"name": "Test Student", "registration_number": reg, "learner_id": lid}

    r = requests.post(f"{A}/register-send-otp", json=body)
    check("register-send-otp 200", r.status_code == 200, r.text)
    otp = r.json().get("test_otp")
    check("dev mode returns 6-digit test_otp", bool(otp) and len(otp) == 6, r.text)

    r = requests.post(f"{A}/register-send-otp", json=body)
    check("resend within 45s -> 429", r.status_code == 429, r.text)

    r = requests.post(f"{A}/register-verify-otp", json={**body, "otp_code": "123456" if otp != "123456" else "654321"})
    check("old 123456 backdoor rejected", r.status_code == 400, r.text)

    r = requests.post(f"{A}/register-verify-otp", json={**body, "registration_number": "220905123", "otp_code": otp})
    check("swapped reg no (year mismatch) rejected at verify", r.status_code == 400, r.text)

    r = requests.post(f"{A}/register-verify-otp", json={**body, "otp_code": otp})
    check("register-verify-otp correct code -> token", r.status_code == 200 and r.json().get("access_token"), r.text)
    token = r.json().get("access_token")
    check("user dict returned", r.json().get("user", {}).get("registration_number") == reg, r.text)

    r = requests.post(f"{A}/register-verify-otp", json={**body, "otp_code": otp})
    check("re-register same details rejected", r.status_code == 400, r.text)

    r = requests.get(f"{A}/me", headers={"Authorization": f"Bearer {token}"})
    check("/me with token", r.status_code == 200 and r.json().get("learner_id") == lid, r.text)

    r = requests.get(f"{A}/me", headers={"Authorization": "Bearer token_forged"})
    check("/me with forged token -> 401", r.status_code == 401, r.text)

    r = requests.post(f"{A}/login-send-otp", json={"identifier": "999999999"})
    check("sign-in unknown identifier -> 404", r.status_code == 404, r.text)

    # sign in with registration number; wait out cooldown first
    print("  waiting 46s for resend cooldown...")
    time.sleep(46)
    r = requests.post(f"{A}/login-send-otp", json={"identifier": reg})
    check("login-send-otp by reg no", r.status_code == 200 and r.json().get("masked_email"), r.text)
    otp2 = r.json().get("test_otp")

    wrong = "000000" if otp2 != "000000" else "111111"
    last = None
    for i in range(5):
        last = requests.post(f"{A}/login-verify-otp", json={"identifier": reg, "otp_code": wrong})
    check("5 wrong codes -> attempts exhausted message", last.status_code == 400 and "Maximum" in last.text, last.text)
    r = requests.post(f"{A}/login-verify-otp", json={"identifier": reg, "otp_code": otp2})
    check("correct code after lockout rejected", r.status_code == 400, r.text)

    print("  waiting 46s for resend cooldown...")
    time.sleep(46)
    r = requests.post(f"{A}/login-send-otp", json={"identifier": lid})
    check("login-send-otp by learner id", r.status_code == 200, r.text)
    otp3 = r.json().get("test_otp")
    r = requests.post(f"{A}/login-verify-otp", json={"identifier": lid, "otp_code": otp3})
    check("login-verify-otp -> token", r.status_code == 200 and r.json().get("access_token"), r.text)
    r = requests.post(f"{A}/login-verify-otp", json={"identifier": lid, "otp_code": otp3})
    check("same code twice rejected", r.status_code == 400, r.text)
    open(sys.argv[3], "w").write(token)

    # The legacy password flow (AuthModal) was removed: sign-in is OTP-only.
    for path in ("verify-learner-id", "verify-otp", "register-complete", "login"):
        r = requests.post(f"{A}/{path}", json={})
        check(f"legacy /{path} removed", r.status_code in (404, 405), r.text)

    r = requests.get(f"{B}/api/admin/monitoring", headers={"Authorization": f"Bearer {token}"})
    check("student token cannot reach admin", r.status_code == 403, r.text)

else:  # after restart
    token = open(sys.argv[3]).read()
    r = requests.get(f"{A}/me", headers={"Authorization": f"Bearer {token}"})
    check("/me with same token after server restart", r.status_code == 200, r.text)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
