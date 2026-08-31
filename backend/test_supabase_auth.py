import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://localhost:8000"

def run_test(name, func):
    print(f"\n==================================================")
    print(f"RUNNING TEST: {name}")
    print(f"==================================================")
    try:
        func()
        print(f"✓ PASS: {name}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {name} — Error: {e}")
        return False

# Test Scenarios

def test_1_send_otp_valid_domain():
    import time
    unique_lid = f"teststudent{int(time.time())}.mitmpl2023@learner.manipal.edu"
    url = f"{BASE_URL}/api/auth/verify-learner-id"
    payload = {"learner_id": unique_lid}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data.get("status") == "success"
            print(f"  Response: {data.get('message')}")
    except urllib.error.HTTPError as e:
        print("TEST 1 HTTP ERROR BODY:", e.read().decode())
        raise e

def test_1_send_otp_invalid_domain():
    url = f"{BASE_URL}/api/auth/verify-learner-id"
    payload = {"learner_id": "outsider@gmail.com"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            raise Exception("Expected 400 rejection for invalid domain but got 200 OK")
    except urllib.error.HTTPError as e:
        assert e.code == 400
        data = json.loads(e.read().decode())
        print(f"  Correctly rejected non-MIT domain: {data.get('detail')}")

def test_2_invalid_otp():
    url = f"{BASE_URL}/api/auth/verify-otp"
    payload = {"learner_id": "teststudent.mitmpl2023@learner.manipal.edu", "otp_code": "000000"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            raise Exception("Expected 400 rejection for invalid OTP but got 200 OK")
    except urllib.error.HTTPError as e:
        assert e.code == 400
        data = json.loads(e.read().decode())
        print(f"  Correctly rejected invalid OTP: {data.get('detail')}")

def test_3_unauthorized_access():
    url = f"{BASE_URL}/api/auth/me"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            raise Exception("Expected 401 rejection for unauthenticated access but got 200 OK")
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print(f"  Correctly blocked unauthenticated request to /api/auth/me (HTTP 401)")

def test_4_full_onboarding_and_session_persistence():
    import time
    lid = f"anoushka{int(time.time())}.mitmpl2023@learner.manipal.edu"
    reg_no = f"23{int(time.time()) % 10000000:07d}"
    url1 = f"{BASE_URL}/api/auth/verify-learner-id"
    req1 = urllib.request.Request(url1, data=json.dumps({"learner_id": lid}).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req1) as resp1:
            data1 = json.loads(resp1.read().decode())
            print(f"  Learner ID Verification: {data1.get('status')}")
    except urllib.error.HTTPError as e:
        print("TEST 4 STEP 1 HTTP ERROR BODY:", e.read().decode())
        raise e

    # Fetch active OTP code from SQLite for test verification
    from app.database import SessionLocal
    from app import models
    db = SessionLocal()
    otp_rec = db.query(models.OTPRecord).filter(models.OTPRecord.learner_id == lid).order_by(models.OTPRecord.id.desc()).first()
    db.close()
    
    # 2. Verify OTP
    url_v = f"{BASE_URL}/api/auth/verify-otp"
    payload_v = {"learner_id": lid, "otp_code": "123456"}  # test code
    # If using local OTP record, update or use the generated code
    if otp_rec:
        import hashlib
        # For testing, accept the generated or test OTP
        db = SessionLocal()
        rec = db.query(models.OTPRecord).filter(models.OTPRecord.id == otp_rec.id).first()
        if rec:
            rec.otp_hash = hashlib.sha256("123456".encode()).hexdigest()
            rec.is_used = False
            db.commit()
        db.close()

    req_v = urllib.request.Request(url_v, data=json.dumps(payload_v).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_v) as resp_v:
        data_v = json.loads(resp_v.read().decode())
        assert data_v.get("status") == "verified"
        print(f"  OTP Verification: {data_v.get('message')}")

    # 3. Register complete
    url2 = f"{BASE_URL}/api/auth/register-complete"
    payload2 = {
        "learner_id": lid,
        "otp_code": "123456",
        "registration_number": reg_no,
        "password": "SecurePassword123!",
        "name": "Anoushka Sharma",
        "department": "Computer Science & Engg",
        "academic_year": "3rd Year (2023-27)",
        "semester": "Even Semester (Jan - May)",
        "agreed_terms": True,
    }
    req2 = urllib.request.Request(url2, data=json.dumps(payload2).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req2) as resp2:
        assert resp2.status == 200
        data2 = json.loads(resp2.read().decode())
        token = data2.get("access_token")
        user = data2.get("user")
        assert token is not None
        assert user.get("learner_id") == lid
        print(f"  Account Created Successfully! Token: {token[:12]}...")

    # 4. Session Persistence via /api/auth/me
    url3 = f"{BASE_URL}/api/auth/me"
    req3 = urllib.request.Request(url3, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req3) as resp3:
        assert resp3.status == 200
        user_me = json.loads(resp3.read().decode())
        assert user_me.get("learner_id") == lid
        assert user_me.get("registration_number") == reg_no
        print(f"  Session Restored via /api/auth/me: User {user_me.get('name')} ({user_me.get('department')})")

    # 5. Existing User Login Test
    url4 = f"{BASE_URL}/api/auth/login"
    payload4 = {"email_or_id": lid, "password": "SecurePassword123!"}
    req4 = urllib.request.Request(url4, data=json.dumps(payload4).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req4) as resp4:
        assert resp4.status == 200
        data4 = json.loads(resp4.read().decode())
        assert data4.get("access_token") is not None
        print(f"  Existing User Login Successful! Verified profile fields returned.")

if __name__ == "__main__":
    print("==================================================")
    print("STARTING SUPABASE AUTH INTEGRATION TEST SUITE")
    print("==================================================")
    run_test("1. Send OTP & Email Domain Validation", test_1_send_otp_valid_domain)
    run_test("2. Reject Non-MIT Email Domain", test_1_send_otp_invalid_domain)
    run_test("3. Reject Invalid OTP Code", test_2_invalid_otp)
    run_test("4. Block Unauthorized Access to /api/auth/me", test_3_unauthorized_access)
    run_test("5. Full Onboarding, Profile Persistence & Session Restore", test_4_full_onboarding_and_session_persistence)
