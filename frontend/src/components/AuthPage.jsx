import React, { useState, useEffect, useRef } from "react";
import "./AuthPage.css";
import {
  registerSendOTP,
  registerVerifyOTP,
  loginSendOTP,
  loginVerifyOTP,
} from "../api";

const BRANCH_MAP = {
  // 2-digit branch codes (9-digit format)
  "01": "Civil Engineering",
  "02": "Chemical Engineering",
  "03": "Mechanical Engineering",
  "04": "Mechatronics Engineering",
  "05": "Computer Science & Engineering",
  "06": "Aeronautical Engineering",
  "07": "Electronics & Communication Engg",
  "08": "Electrical & Electronics Engg",
  "09": "Automobile Engineering",
  "10": "Industrial & Production Engg",
  "11": "Information Technology",
  "12": "Data Science & Engineering",
  "13": "Computer & Communication Engg",
  "14": "Biomedical Engineering",
  "15": "Biotechnology",
  "62": "Computer Science & Engg (AI & ML)",
  // 3-digit branch codes (12-digit format)
  "001": "Civil Engineering",
  "002": "Chemical Engineering",
  "003": "Mechanical Engineering",
  "004": "Mechatronics Engineering",
  "005": "Computer Science & Engineering",
  "006": "Aeronautical Engineering",
  "007": "Electronics & Communication Engg",
  "008": "Electrical & Electronics Engg",
  "009": "Automobile Engineering",
  "010": "Industrial & Production Engg",
  "011": "Information Technology",
  "012": "Data Science & Engineering",
  "013": "Computer & Communication Engg",
  "014": "Biomedical Engineering",
  "015": "Biotechnology",
  "033": "Aeronautical Engineering",
  "062": "Computer Science & Engg (AI & ML)",
};

export default function AuthPage({ onLoginSuccess }) {
  const [mode, setMode] = useState("signin"); // "signin" | "signup"
  const [step, setStep] = useState("form"); // "form" | "otp"

  // Registration Form State
  const [name, setName] = useState("");
  const [regNo, setRegNo] = useState("");
  const [learnerId, setLearnerId] = useState("");

  // Sign In Form State
  const [loginIdentifier, setLoginIdentifier] = useState("");

  // OTP State
  const [otpDigits, setOtpDigits] = useState(["", "", "", "", "", ""]);
  const [otpTargetDisplay, setOtpTargetDisplay] = useState("");
  const [activeLearnerId, setActiveLearnerId] = useState("");
  const [activeIdentifier, setActiveIdentifier] = useState("");
  const [devOtpCode, setDevOtpCode] = useState(null);
  const [cooldown, setCooldown] = useState(0);

  // Status & Error
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const otpInputsRef = useRef([]);

  // Cooldown countdown timer
  useEffect(() => {
    let timer = null;
    if (cooldown > 0) {
      timer = setInterval(() => {
        setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [cooldown]);

  // Derived registration number breakdown (supports 9 or 12 digits)
  const cleanRegNo = regNo.replace(/\D/g, "").slice(0, 12);
  const is12DigitMode = cleanRegNo.length > 9 || (cleanRegNo.length >= 5 && cleanRegNo.slice(2, 5) === "109");

  const year2d = cleanRegNo.slice(0, 2);
  const instCode = is12DigitMode ? cleanRegNo.slice(2, 5) : cleanRegNo.slice(2, 4);
  const branchCode = is12DigitMode ? cleanRegNo.slice(5, 8) : cleanRegNo.slice(4, 6);
  const uniqueId = is12DigitMode ? cleanRegNo.slice(8, 12) : cleanRegNo.slice(6, 9);
  const detectedBranch = BRANCH_MAP[branchCode] || "";

  // Switch tabs
  const handleSwitchMode = (newMode) => {
    setMode(newMode);
    setStep("form");
    setError(null);
    setSuccessMsg(null);
    setOtpDigits(["", "", "", "", "", ""]);
    setDevOtpCode(null);
  };

  // Handle OTP digit changes with auto-advance
  const handleOtpDigitChange = (index, value) => {
    const val = value.replace(/\D/g, "").slice(-1);
    const newDigits = [...otpDigits];
    newDigits[index] = val;
    setOtpDigits(newDigits);

    // Auto-advance to next input
    if (val && index < 5) {
      otpInputsRef.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === "Backspace" && !otpDigits[index] && index > 0) {
      otpInputsRef.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (pasted) {
      const newDigits = [...otpDigits];
      for (let i = 0; i < 6; i++) {
        newDigits[i] = pasted[i] || "";
      }
      setOtpDigits(newDigits);
      const nextFocus = Math.min(pasted.length, 5);
      otpInputsRef.current[nextFocus]?.focus();
    }
  };

  // 1. Submit Registration Form -> Send OTP
  const handleRegisterSendOTP = async (e) => {
    e?.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!name.trim()) {
      setError("Please enter your full name.");
      return;
    }

    if (cleanRegNo.length !== 9 && cleanRegNo.length !== 12) {
      setError("Registration Number must be either 9 digits (e.g. 230962088) or 12 digits (e.g. 261090330156).");
      return;
    }

    if (cleanRegNo.length === 9 && instCode !== "09") {
      setError("Digits 3–4 must be '09' for MAHE MIT Manipal campus (9-digit format).");
      return;
    }

    if (cleanRegNo.length === 12 && instCode !== "109") {
      setError("Digits 3–5 must be '109' for MAHE MIT Manipal campus (12-digit format).");
      return;
    }

    const lid = learnerId.trim().toLowerCase();
    if (!lid.includes("@learner.manipal.edu") && !lid.includes("@manipal.edu")) {
      setError("Learner ID must end with @learner.manipal.edu (e.g. anoushka1.mitmpl2023@learner.manipal.edu).");
      return;
    }

    // Check year consistency
    const yearMatch = lid.match(/20\d{2}/);
    if (yearMatch && yearMatch[0].slice(-2) !== year2d) {
      setError(
        `Admission year mismatch: Registration Number starts with '${year2d}' (20${year2d}), but Learner ID specifies ${yearMatch[0]}.`
      );
      return;
    }

    setLoading(true);
    try {
      const res = await registerSendOTP({
        name: name.trim(),
        registration_number: cleanRegNo,
        learner_id: lid,
      });

      setActiveLearnerId(lid);
      setOtpTargetDisplay(lid);
      setDevOtpCode(res.test_otp || null);
      setCooldown(45);
      setStep("otp");
      setSuccessMsg(res.message || `OTP sent to ${lid}`);
    } catch (err) {
      setError(err.message || "Failed to dispatch registration OTP.");
    } finally {
      setLoading(false);
    }
  };

  // 2. Verify Registration OTP -> Complete & Enter
  const handleRegisterVerifyOTP = async (e) => {
    e?.preventDefault();
    setError(null);
    const code = otpDigits.join("");
    if (code.length !== 6) {
      setError("Please enter the complete 6-digit OTP code.");
      return;
    }

    setLoading(true);
    try {
      const res = await registerVerifyOTP({
        name: name.trim(),
        registration_number: cleanRegNo,
        learner_id: activeLearnerId,
        otp_code: code,
      });

      // Save tokens and login
      if (res.access_token) {
        localStorage.setItem("campus_token", res.access_token);
        localStorage.setItem("campus_user", JSON.stringify(res.user));
      }
      onLoginSuccess(res.user);
    } catch (err) {
      setError(err.message || "OTP verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // 3. Submit Sign In Form -> Send OTP
  const handleLoginSendOTP = async (e) => {
    e?.preventDefault();
    setError(null);
    setSuccessMsg(null);

    const ident = loginIdentifier.trim();
    if (!ident) {
      setError("Please enter your Learner ID or 9-digit Registration Number.");
      return;
    }

    setLoading(true);
    try {
      const res = await loginSendOTP(ident);
      setActiveIdentifier(ident);
      setActiveLearnerId(res.learner_id || ident);
      setOtpTargetDisplay(res.masked_email || res.learner_id || ident);
      setDevOtpCode(res.test_otp || null);
      setCooldown(45);
      setStep("otp");
      setSuccessMsg(res.message || "Verification code dispatched.");
    } catch (err) {
      setError(err.message || "Failed to send sign-in OTP.");
    } finally {
      setLoading(false);
    }
  };

  // 4. Verify Sign In OTP -> Complete & Enter
  const handleLoginVerifyOTP = async (e) => {
    e?.preventDefault();
    setError(null);
    const code = otpDigits.join("");
    if (code.length !== 6) {
      setError("Please enter the complete 6-digit OTP code.");
      return;
    }

    setLoading(true);
    try {
      const res = await loginVerifyOTP(activeIdentifier, code);
      if (res.access_token) {
        localStorage.setItem("campus_token", res.access_token);
        localStorage.setItem("campus_user", JSON.stringify(res.user));
      }
      onLoginSuccess(res.user);
    } catch (err) {
      setError(err.message || "Invalid OTP code. Please check and re-enter.");
    } finally {
      setLoading(false);
    }
  };

  // Resend OTP
  const handleResendOTP = async () => {
    if (cooldown > 0) return;
    setError(null);
    setSuccessMsg(null);
    setLoading(true);
    try {
      if (mode === "signup") {
        const res = await registerSendOTP({
          name: name.trim(),
          registration_number: cleanRegNo,
          learner_id: activeLearnerId,
        });
        setDevOtpCode(res.test_otp || null);
        setSuccessMsg(`New OTP sent to ${activeLearnerId}`);
      } else {
        const res = await loginSendOTP(activeIdentifier);
        setDevOtpCode(res.test_otp || null);
        setSuccessMsg(`New OTP sent to ${otpTargetDisplay}`);
      }
      setCooldown(45);
      setOtpDigits(["", "", "", "", "", ""]);
    } catch (err) {
      setError(err.message || "Failed to resend OTP.");
    } finally {
      setLoading(false);
    }
  };

  // Quick Instant Demo Login
  const handleQuickDemoLogin = (roleType) => {
    const demoProfiles = {
      student: {
        id: "demo_student_aarav",
        name: "Aarav Sharma",
        email: "aarav.mitmpl2023@learner.manipal.edu",
        learner_id: "aarav.mitmpl2023@learner.manipal.edu",
        registration_number: "230962088",
        admission_year: "2023",
        role: "student",
        is_verified: true,
        account_state: "Verified",
        department: "Computer Science & Engg (AI & ML)",
        academic_year: "3rd Year (2023-27)",
        semester: "Even Semester (Jan - May)",
        rewards_points: 1240,
        avatar_icon: "🎓",
        status: "active",
      },
      faculty: {
        id: "demo_faculty_radhika",
        name: "Dr. Radhika Pai",
        email: "radhika.pai@manipal.edu",
        role: "faculty",
        is_verified: true,
        account_state: "Verified",
        department: "Computer Science & Engineering",
        academic_year: "Faculty Member",
        avatar_icon: "👨‍🏫",
        status: "active",
      },
      admin: {
        id: "demo_admin_root",
        name: "MAHE System Administrator",
        email: "admin@manipal.edu",
        role: "admin",
        is_verified: true,
        account_state: "Verified",
        department: "Directorate of IT & Systems",
        avatar_icon: "👑",
        status: "active",
      },
    };

    const selected = demoProfiles[roleType] || demoProfiles.student;
    const dummyToken = `demo_token_${roleType}_${Date.now()}`;
    localStorage.setItem("campus_token", dummyToken);
    localStorage.setItem("campus_user", JSON.stringify(selected));
    onLoginSuccess(selected);
  };

  return (
    <div className="auth-page-shell">
      {/* Left Form Column */}
      <main className="auth-page-main">
        <div className="auth-page-card">
          {/* Brand Header */}
          <div className="auth-page-brand">
            <div className="auth-brand-badge">
              <span className="auth-brand-mark">M</span>
              <span>
                MIT<span className="auth-brand-accent">ra</span> CampusOS
              </span>
            </div>
            <span className="auth-campus-tag">MAHE Manipal</span>
          </div>

          <p className="auth-kicker">
            {mode === "signin" ? "STUDENT ACCESS" : "STUDENT ONBOARDING"}
          </p>
          <h1 className="auth-heading">
            {step === "otp"
              ? "Verify OTP code"
              : mode === "signin"
              ? "Welcome back."
              : "Create student account."}
          </h1>
          <p className="auth-subheading">
            {step === "otp"
              ? `Enter the 6-digit verification code dispatched to ${otpTargetDisplay}.`
              : mode === "signin"
              ? "Enter your Learner ID or 9-digit Registration Number to sign in with OTP."
              : "Register with your verified Manipal identity. Passwordless, secure OTP authentication."}
          </p>

          {/* Mode Switch Tabs (only visible on form step) */}
          {step === "form" && (
            <div className="auth-mode-tabs">
              <button
                type="button"
                className={`auth-mode-tab ${mode === "signin" ? "active" : ""}`}
                onClick={() => handleSwitchMode("signin")}
              >
                Sign In
              </button>
              <button
                type="button"
                className={`auth-mode-tab ${mode === "signup" ? "active" : ""}`}
                onClick={() => handleSwitchMode("signup")}
              >
                Create Account
              </button>
            </div>
          )}

          {/* Feedback Banners */}
          {error && <div className="auth-error-alert">⚠️ {error}</div>}
          {successMsg && <div className="auth-success-alert">✓ {successMsg}</div>}

          {/* Dev Mode OTP helper banner */}
          {devOtpCode && step === "otp" && (
            <div className="auth-dev-alert">
              <span>
                🛠️ <strong>Development OTP:</strong>
              </span>
              <span className="auth-dev-code">{devOtpCode}</span>
            </div>
          )}

          {/* ---------------- FORM STEP ---------------- */}
          {step === "form" && (
            <>
              {mode === "signin" ? (
                /* SIGN IN FORM */
                <form onSubmit={handleLoginSendOTP}>
                  <div className="auth-field">
                    <label className="auth-field-label">
                      Learner ID or Registration Number
                      <span className="auth-field-hint">e.g. 230962088</span>
                    </label>
                    <input
                      type="text"
                      className="auth-text-input"
                      placeholder="e.g. anoushka1.mitmpl2023@learner.manipal.edu or 230962088"
                      value={loginIdentifier}
                      onChange={(e) => setLoginIdentifier(e.target.value)}
                      required
                      autoFocus
                    />
                  </div>

                  <button
                    type="submit"
                    className="auth-action-btn"
                    disabled={loading || !loginIdentifier.trim()}
                  >
                    {loading ? "Sending OTP..." : "Send Verification OTP →"}
                  </button>
                </form>
              ) : (
                /* SIGN UP FORM */
                <form onSubmit={handleRegisterSendOTP}>
                  <div className="auth-field">
                    <label className="auth-field-label">
                      Full Name
                      <span className="auth-field-hint">As per college records</span>
                    </label>
                    <input
                      type="text"
                      className="auth-text-input"
                      placeholder="e.g. Anoushka Sharma"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                      autoFocus
                    />
                  </div>

                  <div className="auth-field">
                    <label className="auth-field-label">
                      Registration Number (9 or 12 Digits)
                      <span className="auth-field-hint">e.g. 230962088 or 261090330156</span>
                    </label>
                    <input
                      type="text"
                      maxLength={12}
                      className="auth-text-input"
                      placeholder="e.g. 230962088 or 261090330156"
                      value={regNo}
                      onChange={(e) => setRegNo(e.target.value.replace(/\D/g, ""))}
                      required
                    />
                  </div>

                  {/* Visual 9 or 12 Digit Breakdown Card */}
                  {cleanRegNo.length > 0 && (
                    <div className="reg-breakdown-card">
                      <div className="reg-breakdown-title">
                        <span>
                          Structure ({is12DigitMode ? "12-Digit Format" : "9-Digit Format"})
                        </span>
                        <span>{cleanRegNo.length} / {is12DigitMode ? 12 : 9} digits</span>
                      </div>
                      <div className="reg-digits-grid">
                        <div className={`reg-digit-box ${year2d.length === 2 ? "valid" : "filled"}`}>
                          <div className="reg-digit-val">{year2d || "··"}</div>
                          <div className="reg-digit-label">
                            {year2d.length === 2 ? `Year 20${year2d}` : "1-2: Year"}
                          </div>
                        </div>

                        <div className={`reg-digit-box ${(is12DigitMode ? instCode === "109" : instCode === "09") ? "valid" : instCode ? "filled" : ""}`}>
                          <div className="reg-digit-val">{instCode || (is12DigitMode ? "···" : "··")}</div>
                          <div className="reg-digit-label">
                            {is12DigitMode ? "3-5: 109 Campus" : "3-4: 09 Campus"}
                          </div>
                        </div>

                        <div className={`reg-digit-box ${(is12DigitMode ? branchCode.length === 3 : branchCode.length === 2) ? "valid" : branchCode ? "filled" : ""}`}>
                          <div className="reg-digit-val">{branchCode || (is12DigitMode ? "···" : "··")}</div>
                          <div className="reg-digit-label">
                            {is12DigitMode ? "6-8: Branch" : "5-6: Branch"}
                          </div>
                        </div>

                        <div className={`reg-digit-box ${(is12DigitMode ? uniqueId.length === 4 : uniqueId.length === 3) ? "valid" : uniqueId ? "filled" : ""}`}>
                          <div className="reg-digit-val">{uniqueId || (is12DigitMode ? "····" : "···")}</div>
                          <div className="reg-digit-label">
                            {is12DigitMode ? "9-12: Student ID" : "7-9: Student ID"}
                          </div>
                        </div>
                      </div>

                      {detectedBranch && (
                        <div className="reg-detected-row">
                          <span>Detected Department:</span>
                          <span className="reg-branch-badge">{detectedBranch}</span>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="auth-field">
                    <label className="auth-field-label">
                      Learner ID Email
                      <span className="auth-field-hint">name.mitmplYYYY@learner.manipal.edu</span>
                    </label>
                    <input
                      type="email"
                      className="auth-text-input"
                      placeholder={`e.g. name.mitmpl${year2d ? `20${year2d}` : "2023"}@learner.manipal.edu`}
                      value={learnerId}
                      onChange={(e) => setLearnerId(e.target.value)}
                      required
                    />
                  </div>

                  <button
                    type="submit"
                    className="auth-action-btn"
                    disabled={loading || !name || (cleanRegNo.length !== 9 && cleanRegNo.length !== 12) || !learnerId}
                  >
                    {loading ? "Sending OTP..." : "Send Verification OTP to Learner ID →"}
                  </button>
                </form>
              )}
            </>
          )}

          {/* ---------------- OTP VERIFICATION STEP ---------------- */}
          {step === "otp" && (
            <div className="otp-card-shell">
              <p className="otp-target-info">
                We sent a 6-digit authentication code to:
                <br />
                <strong>{otpTargetDisplay}</strong>
              </p>

              {/* 6 Digit Cells */}
              <div className="otp-input-row" onPaste={handleOtpPaste}>
                {otpDigits.map((digit, i) => (
                  <input
                    key={i}
                    ref={(el) => (otpInputsRef.current[i] = el)}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    className="otp-digit-cell"
                    value={digit}
                    onChange={(e) => handleOtpDigitChange(i, e.target.value)}
                    onKeyDown={(e) => handleOtpKeyDown(i, e)}
                    autoFocus={i === 0}
                  />
                ))}
              </div>

              {/* Timer & Resend */}
              <div className="otp-timer-row">
                <span>
                  {cooldown > 0 ? `Resend code in ${cooldown}s` : "Didn't receive the email?"}
                </span>
                <button
                  type="button"
                  className="otp-resend-btn"
                  onClick={handleResendOTP}
                  disabled={cooldown > 0 || loading}
                >
                  Resend OTP
                </button>
              </div>

              <button
                type="button"
                className="auth-action-btn"
                onClick={mode === "signup" ? handleRegisterVerifyOTP : handleLoginVerifyOTP}
                disabled={loading || otpDigits.join("").length !== 6}
                style={{ marginTop: "20px" }}
              >
                {loading
                  ? "Verifying..."
                  : mode === "signup"
                  ? "Verify & Create Account →"
                  : "Verify & Enter CampusOS →"}
              </button>

              <button
                type="button"
                className="auth-secondary-btn"
                onClick={() => {
                  setStep("form");
                  setError(null);
                  setSuccessMsg(null);
                }}
              >
                ← Back to Edit Details
              </button>
            </div>
          )}

          {/* Quick Demo Access Bar for effortless testing */}
          <div className="auth-demo-section">
            <div className="auth-demo-title">Fast Demo Profiles (Instant Test)</div>
            <div className="auth-demo-chips">
              <button
                type="button"
                className="auth-demo-chip"
                onClick={() => handleQuickDemoLogin("student")}
              >
                🎓 Student (Aarav - CSE AIML)
              </button>
              <button
                type="button"
                className="auth-demo-chip"
                onClick={() => handleQuickDemoLogin("faculty")}
              >
                👨‍🏫 Faculty (Dr. Radhika Pai)
              </button>
              <button
                type="button"
                className="auth-demo-chip"
                onClick={() => handleQuickDemoLogin("admin")}
              >
                👑 System Admin
              </button>
            </div>
          </div>

          <p className="auth-footer-notes">
            MAHE MIT Manipal · CampusOS Institutional Intelligence
            <br />
            Strictly restricted to authorized students and institutional personnel.
          </p>
        </div>
      </main>

      {/* Right Editorial Brand Column (Mitra Style) */}
      <aside className="auth-page-side">
        <div className="auth-side-decor-circle" />

        <div className="auth-side-top">
          <div className="auth-quote-mark">“</div>
          <blockquote className="auth-side-quote">
            The best campus experiences often start with a simple question.
          </blockquote>
          <span className="auth-side-author">— MITra, your campus companion</span>
        </div>

        <div className="auth-side-features">
          <div className="auth-side-feature-item">
            <span className="auth-side-feature-icon">🏛️</span>
            <div>
              <strong>Official University Grounding</strong>
              <div>Syllabi, academic calendars, cutoffs, and faculty cabins.</div>
            </div>
          </div>

          <div className="auth-side-feature-item">
            <span className="auth-side-feature-icon">💬</span>
            <div>
              <strong>Student Corner Community</strong>
              <div>Verified senior advice across 11 sub-community channels.</div>
            </div>
          </div>

          <div className="auth-side-feature-item">
            <span className="auth-side-feature-icon">🔐</span>
            <div>
              <strong>Student Privacy & Safety</strong>
              <div>Passwordless OTP authentication tied to verified Learner IDs.</div>
            </div>
          </div>
        </div>

        <div className="auth-side-footer">
          <span>MIT Manipal © 2026 CampusOS</span>
          <div className="auth-side-dots">
            <span className="auth-side-dot active" />
            <span className="auth-side-dot" />
            <span className="auth-side-dot" />
          </div>
        </div>
      </aside>
    </div>
  );
}
