import React, { useState, useEffect, useRef } from "react";
import {
  verifyLearnerID,
  verifyOTPCode,
  completeRegistration,
  loginUser,
  fetchDepartments,
} from "../api";
import TermsModal from "./TermsModal";

// Six-box OTP entry: auto-advances on digit, auto-backs on empty backspace,
// and accepts a full 6-digit paste into any box.
//
// Each box's displayed digit comes from its own slot in local state, not from
// re-slicing the joined `value` string — joining a 6-slot array where an early
// slot is empty silently collapses/shifts the remaining digits leftward
// (e.g. clearing box 0 of "123456" would show "23456_" instead of "_23456"),
// which corrupts the code the moment a user fixes a typo in an earlier digit.
function OTPInputBoxes({ value, onChange, disabled }) {
  const refs = useRef([]);
  const [slots, setSlots] = useState(() => Array.from({ length: 6 }, (_, i) => value[i] || ""));

  // External resets (e.g. resend clears otpCode) should clear the boxes too.
  useEffect(() => {
    if (value === "") setSlots(Array(6).fill(""));
  }, [value]);

  const focusBox = (i) => refs.current[i]?.focus();

  const commit = (newSlots) => {
    setSlots(newSlots);
    onChange(newSlots.join(""));
  };

  const handleChange = (idx, e) => {
    const val = e.target.value.replace(/\D/g, "").slice(-1);
    const next = [...slots];
    next[idx] = val;
    commit(next);
    if (val && idx < 5) focusBox(idx + 1);
  };

  const handleKeyDown = (idx, e) => {
    if (e.key === "Backspace" && !slots[idx] && idx > 0) {
      focusBox(idx - 1);
    }
  };

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (!pasted) return;
    e.preventDefault();
    commit(Array.from({ length: 6 }, (_, i) => pasted[i] || ""));
    focusBox(Math.min(pasted.length, 6) - 1);
  };

  return (
    <div className="otp-input-group" onPaste={handlePaste}>
      {slots.map((d, i) => (
        <input
          key={i}
          ref={(el) => (refs.current[i] = el)}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={1}
          className="otp-box"
          value={d}
          onChange={(e) => handleChange(i, e)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          disabled={disabled}
          autoFocus={i === 0}
          aria-label={`OTP digit ${i + 1} of 6`}
        />
      ))}
    </div>
  );
}

export default function AuthModal({ isOpen, onClose, onLoginSuccess }) {
  const [tab, setTab] = useState("login"); // "login" | "signup"

  // Login State
  const [loginIdentifier, setLoginIdentifier] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Step Wizard State (1: Learner ID, 2: OTP, 3: Reg No & Password, 4: Academic Details & Terms)
  const [step, setStep] = useState(1);
  const [learnerId, setLearnerId] = useState("");
  const [admissionYear, setAdmissionYear] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [regNumber, setRegNumber] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [department, setDepartment] = useState("Computer Science & Engineering");
  const [academicYear, setAcademicYear] = useState("3rd Year (2023-27)");
  const [semester, setSemester] = useState("Even Semester (Jan - May)");
  const [agreedTerms, setAgreedTerms] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);

  // Departments List from backend
  const [departmentsList, setDepartmentsList] = useState([]);

  // Timers
  const [otpTimer, setOtpTimer] = useState(600);
  const [cooldown, setCooldown] = useState(0);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    if (isOpen) {
      loadDeptList();
    }
  }, [isOpen]);

  const loadDeptList = async () => {
    const data = await fetchDepartments();
    if (data && data.departments) {
      setDepartmentsList(data.departments);
    }
  };

  useEffect(() => {
    let timerInterval, cooldownInterval;
    if (step === 2 && otpTimer > 0) {
      timerInterval = setInterval(() => setOtpTimer((t) => (t > 0 ? t - 1 : 0)), 1000);
    }
    if (cooldown > 0) {
      cooldownInterval = setInterval(() => setCooldown((c) => (c > 0 ? c - 1 : 0)), 1000);
    }
    return () => {
      clearInterval(timerInterval);
      clearInterval(cooldownInterval);
    };
  }, [step, otpTimer, cooldown]);

  if (!isOpen) return null;

  // Step 1: Validate Learner ID and Send Real OTP
  const handleStep1VerifyLearnerID = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setLoading(true);
    try {
      const data = await verifyLearnerID(learnerId);
      setAdmissionYear(data.admission_year || "2023");
      setSuccessMsg(`Verification OTP sent to ${learnerId}. Please check your email.`);
      setOtpTimer(600);
      setCooldown(60);
      setStep(2);
    } catch (err) {
      setError(err.message || "Failed to verify Learner ID.");
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP
  const handleStep2VerifyOTP = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await verifyOTPCode(learnerId, otpCode);
      setSuccessMsg("OTP verified successfully! Now enter your 9-digit Registration Number.");
      setStep(3);
    } catch (err) {
      setError(err.message || "OTP verification failed.");
    } finally {
      setLoading(false);
    }
  };

  // Resend OTP Handler
  const handleResendOTP = async () => {
    if (cooldown > 0) return;
    setError("");
    setLoading(true);
    try {
      await verifyLearnerID(learnerId);
      setSuccessMsg(`New OTP sent to ${learnerId}.`);
      setOtpCode("");
      setOtpTimer(600);
      setCooldown(60);
    } catch (err) {
      setError(err.message || "Failed to resend OTP.");
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Advance to Step 4 (Academic Info & Terms)
  const handleStep3RegAndPass = (e) => {
    e.preventDefault();
    setError("");
    if (!/^\d{9}$/.test(regNumber.trim())) {
      setError("Registration Number must be a unique 9-digit numeric identifier (e.g. 230911042).");
      return;
    }
    if (!password || password.length < 6) {
      setError("Password must be at least 6 characters in length.");
      return;
    }
    setStep(4);
  };

  // Step 4: Final Complete Registration
  const handleStep4CompleteRegistration = async (e) => {
    e.preventDefault();
    if (!agreedTerms) {
      setError("You must explicitly accept the Terms & Conditions and Community Guidelines to create an account.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const payload = {
        learner_id: learnerId.trim().toLowerCase(),
        otp_code: otpCode.trim(),
        registration_number: regNumber.trim(),
        password: password,
        name: fullName.trim() || "Student",
        department: department,
        academic_year: academicYear,
        semester: semester,
        agreed_terms: agreedTerms,
      };

      const response = await completeRegistration(payload);
      onLoginSuccess(response.user, response.access_token);
      onClose();
    } catch (err) {
      setError(err.message || "Account creation failed.");
    } finally {
      setLoading(false);
    }
  };

  // Login Handler
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await loginUser(loginIdentifier.trim().toLowerCase(), loginPassword);
      onLoginSuccess(response.user, response.access_token);
      onClose();
    } catch (err) {
      setError(err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  const formatTimer = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="auth-modal-card fade-in" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "520px" }}>
        {/* Modal Header */}
        <div className="auth-modal-header">
          <div className="auth-brand">
            <span className="brand-badge">MAHE MIT</span>
            <span className="auth-title">CampusOS Student Authentication</span>
          </div>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Tab Switcher */}
        <div className="auth-tabs" style={{ marginTop: "14px" }}>
          <button
            className={`auth-tab ${tab === "login" ? "active" : ""}`}
            onClick={() => {
              setTab("login");
              setError("");
              setSuccessMsg("");
            }}
          >
            Sign In
          </button>
          <button
            className={`auth-tab ${tab === "signup" ? "active" : ""}`}
            onClick={() => {
              setTab("signup");
              setStep(1);
              setError("");
              setSuccessMsg("");
            }}
          >
            Student Onboarding & Verification
          </button>
        </div>

        {error && <div className="auth-error-alert" style={{ marginTop: "12px" }}>⚠️ {error}</div>}
        {successMsg && <div className="auth-success-alert" style={{ marginTop: "12px", padding: "10px", background: "#F0FDF4", border: "1px solid #BBF7D0", color: "#166534", borderRadius: "8px", fontSize: "12px" }}>✓ {successMsg}</div>}

        {/* 1. SIGN IN FORM */}
        {tab === "login" && (
          <form onSubmit={handleLoginSubmit} className="auth-form" style={{ marginTop: "14px" }}>
            <div className="form-group">
              <label style={{ fontWeight: 700 }}>Learner ID / Registration Number:</label>
              <input
                type="text"
                required
                placeholder="yourname.mitmpl2023@learner.manipal.edu or 230911042"
                value={loginIdentifier}
                onChange={(e) => setLoginIdentifier(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label style={{ fontWeight: 700 }}>Password:</label>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
              />
            </div>

            <button type="submit" className="auth-submit-btn" disabled={loading}>
              {loading ? "Authenticating..." : "Sign In to Student Workspace 🎓"}
            </button>
          </form>
        )}

        {/* 2. ONBOARDING WIZARD */}
        {tab === "signup" && (
          <div className="verification-flow-container" style={{ marginTop: "14px" }}>
            {/* Step Indicators */}
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "14px", fontSize: "11px", fontWeight: 700, color: "#64748B" }}>
              <span style={{ color: step >= 1 ? "#2563EB" : "#94A3B8" }}>1. Learner ID</span>
              <span style={{ color: step >= 2 ? "#2563EB" : "#94A3B8" }}>2. OTP</span>
              <span style={{ color: step >= 3 ? "#2563EB" : "#94A3B8" }}>3. Reg No & Password</span>
              <span style={{ color: step >= 4 ? "#2563EB" : "#94A3B8" }}>4. Profile & Terms</span>
            </div>

            {/* STEP 1: LEARNER ID INPUT */}
            {step === 1 && (
              <form onSubmit={handleStep1VerifyLearnerID} className="auth-form">
                <div className="form-group">
                  <label style={{ fontWeight: 800 }}>Enter Complete Manipal Learner ID:</label>
                  <input
                    type="email"
                    required
                    placeholder="yourname.mitmpl2023@learner.manipal.edu"
                    value={learnerId}
                    onChange={(e) => setLearnerId(e.target.value)}
                    style={{ fontSize: "14px", fontWeight: 600 }}
                  />
                  <small style={{ color: "#64748B", fontSize: "11px", marginTop: "4px", display: "block" }}>
                    Must follow format: <code>&lt;name&gt;.mitmpl&lt;year&gt;@learner.manipal.edu</code>
                  </small>
                </div>

                <button type="submit" className="auth-submit-btn" disabled={loading}>
                  {loading ? "Sending OTP Code..." : "Verify Learner ID & Send OTP →"}
                </button>
              </form>
            )}

            {/* STEP 2: OTP VERIFICATION */}
            {step === 2 && (
              <form onSubmit={handleStep2VerifyOTP} className="auth-form">
                <div style={{ padding: "12px", background: "#F8FAFC", border: "1px solid #E2E8F0", borderRadius: "8px", textAlign: "center", marginBottom: "12px" }}>
                  <span style={{ fontSize: "20px" }}>📩</span>
                  <h4 style={{ margin: "4px 0 0 0", fontSize: "14px", fontWeight: 800 }}>Enter 6-Digit OTP Code</h4>
                  <p style={{ margin: "2px 0 0 0", fontSize: "11px", color: "#64748B" }}>
                    OTP code was dispatched to <strong>{learnerId}</strong>.
                  </p>
                </div>

                <div className="form-group">
                  <OTPInputBoxes value={otpCode} onChange={setOtpCode} disabled={loading || otpTimer === 0} />
                  {otpTimer === 0 && (
                    <div className="auth-error-alert" style={{ marginTop: "10px" }}>
                      ⚠️ This code has expired. Request a new one below.
                    </div>
                  )}
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px", marginBottom: "12px" }}>
                  <span style={{ color: otpTimer < 60 ? "#DC2626" : "#475569", fontWeight: 700 }}>
                    ⏱️ Code Expires: {formatTimer(otpTimer)}
                  </span>
                  <button
                    type="button"
                    onClick={handleResendOTP}
                    disabled={cooldown > 0}
                    style={{ background: "none", border: "none", color: cooldown > 0 ? "#94A3B8" : "#2563EB", fontWeight: 800, cursor: cooldown > 0 ? "not-allowed" : "pointer" }}
                  >
                    {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend OTP 🔄"}
                  </button>
                </div>

                <button type="submit" className="auth-submit-btn" disabled={loading || otpTimer === 0 || otpCode.length !== 6}>
                  {loading ? "Verifying OTP..." : "Verify OTP Code →"}
                </button>
              </form>
            )}

            {/* STEP 3: 9-DIGIT REGISTRATION NUMBER & PASSWORD */}
            {step === 3 && (
              <form onSubmit={handleStep3RegAndPass} className="auth-form">
                <div className="form-group">
                  <label style={{ fontWeight: 800 }}>Verified Learner ID (Read-only):</label>
                  <input type="text" disabled value={learnerId} style={{ background: "#F1F5F9", color: "#475569", fontWeight: 700 }} />
                </div>

                <div className="form-group">
                  <label style={{ fontWeight: 800 }}>Extracted Admission Year (Read-only):</label>
                  <input type="text" disabled value={admissionYear} style={{ background: "#F1F5F9", color: "#475569", fontWeight: 700 }} />
                </div>

                <div className="form-group">
                  <label style={{ fontWeight: 800 }}>Enter 9-Digit Registration Number:</label>
                  <input
                    type="text"
                    required
                    maxLength={9}
                    placeholder="e.g. 230911042"
                    value={regNumber}
                    onChange={(e) => setRegNumber(e.target.value)}
                    style={{ fontSize: "15px", letterSpacing: "1px", fontWeight: 700 }}
                  />
                  <small style={{ color: "#64748B", fontSize: "11px" }}>Unique 9-digit numerical identifier.</small>
                </div>

                <div className="form-group">
                  <label style={{ fontWeight: 800 }}>Create Password:</label>
                  <input
                    type="password"
                    required
                    minLength={6}
                    placeholder="Minimum 6 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>

                <button type="submit" className="auth-submit-btn">
                  Continue to Academic Info & Terms →
                </button>
              </form>
            )}

            {/* STEP 4: ACADEMIC DETAILS, PROFILE & TERMS */}
            {step === 4 && (
              <form onSubmit={handleStep4CompleteRegistration} className="auth-form">
                <div className="form-group">
                  <label style={{ fontWeight: 800 }}>Full Name:</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Alex Johnson"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label style={{ fontWeight: 800 }}>Branch / Department:</label>
                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    style={{ padding: "8px", borderRadius: "6px", border: "1px solid #CBD5E1", fontSize: "13px" }}
                  >
                    {departmentsList.length > 0 ? (
                      departmentsList.map((d) => (
                        <option key={d.code} value={d.name}>
                          {d.name} ({d.code})
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="Computer Science & Engineering">Computer Science & Engineering</option>
                        <option value="Information Technology">Information Technology</option>
                        <option value="Data Science & Engineering">Data Science & Engineering</option>
                        <option value="Artificial Intelligence & Machine Learning">Artificial Intelligence & Machine Learning</option>
                        <option value="Electronics & Communication Engineering">Electronics & Communication Engineering</option>
                        <option value="Mechanical Engineering">Mechanical Engineering</option>
                        <option value="Biotechnology">Biotechnology</option>
                      </>
                    )}
                  </select>
                </div>

                <div className="form-group">
                  <label style={{ fontWeight: 800 }}>Current Academic Year:</label>
                  <select
                    value={academicYear}
                    onChange={(e) => setAcademicYear(e.target.value)}
                    style={{ padding: "8px", borderRadius: "6px", border: "1px solid #CBD5E1", fontSize: "13px" }}
                  >
                    <option value="1st Year (2025-29)">1st Year (2025-29)</option>
                    <option value="2nd Year (2024-28)">2nd Year (2024-28)</option>
                    <option value="3rd Year (2023-27)">3rd Year (2023-27)</option>
                    <option value="4th Year (2022-26)">4th Year (2022-26)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label style={{ fontWeight: 800 }}>Current Semester:</label>
                  <select
                    value={semester}
                    onChange={(e) => setSemester(e.target.value)}
                    style={{ padding: "8px", borderRadius: "6px", border: "1px solid #CBD5E1", fontSize: "13px" }}
                  >
                    <option value="Odd Semester (Jul - Dec)">Odd Semester (Jul - Dec)</option>
                    <option value="Even Semester (Jan - May)">Even Semester (Jan - May)</option>
                  </select>
                </div>

                {/* Terms Acceptance Checkbox */}
                <div style={{ margin: "14px 0", padding: "10px", background: "#F8FAFC", border: "1px solid #CBD5E1", borderRadius: "8px" }}>
                  <label style={{ display: "flex", alignItems: "flex-start", gap: "8px", cursor: "pointer", fontSize: "11px", lineHeight: "1.4" }}>
                    <input
                      type="checkbox"
                      checked={agreedTerms}
                      onChange={(e) => setAgreedTerms(e.target.checked)}
                      style={{ marginTop: "2px", width: "16px", height: "16px", cursor: "pointer" }}
                    />
                    <span>
                      I explicitly accept the{" "}
                      <button
                        type="button"
                        onClick={() => setShowTermsModal(true)}
                        style={{ background: "none", border: "none", color: "#2563EB", textDecoration: "underline", fontWeight: 700, padding: 0, cursor: "pointer", fontSize: "11px" }}
                      >
                        Terms & Conditions and Community Guidelines
                      </button>.
                    </span>
                  </label>
                </div>

                <button type="submit" className="auth-submit-btn" disabled={loading || !agreedTerms}>
                  {loading ? "Creating Verified Account..." : "Complete Registration & Enter Workspace 🎓"}
                </button>
              </form>
            )}
          </div>
        )}
      </div>

      {/* Terms & Conditions Modal */}
      <TermsModal isOpen={showTermsModal} onClose={() => setShowTermsModal(false)} />
    </div>
  );
}
