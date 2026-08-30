import React from "react";

export default function TermsModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="auth-overlay" onClick={onClose} style={{ zIndex: 1100 }}>
      <div className="auth-modal-card fade-in" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "580px", maxHeight: "85vh", display: "flex", flexDirection: "column" }}>
        {/* Header */}
        <div className="auth-modal-header" style={{ paddingBottom: "12px", borderBottom: "1px solid #E2E8F0" }}>
          <div className="auth-brand">
            <span className="brand-badge">MAHE</span>
            <span className="auth-title">Terms & Community Guidelines (v1.0-2026)</span>
          </div>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Scrollable Terms Content */}
        <div style={{ overflowY: "auto", padding: "16px 4px", fontSize: "12px", color: "#334155", lineHeight: "1.6" }}>
          <div style={{ padding: "10px 14px", background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "8px", marginBottom: "14px", color: "#1D4ED8", fontWeight: 700 }}>
            📌 Please read these terms carefully before creating or activating your MIT CampusOS verified student account.
          </div>

          <h4 style={{ fontSize: "13px", fontWeight: 800, color: "#0F172A", margin: "12px 0 4px 0" }}>1. Account Responsibility & Credential Security</h4>
          <p>
            Users are solely responsible for keeping their account login credentials confidential and secure. You agree not to share your account access or allow third parties to operate under your registered identity.
          </p>

          <h4 style={{ fontSize: "13px", fontWeight: 800, color: "#0F172A", margin: "12px 0 4px 0" }}>2. Accurate Information & Authentic Learner ID</h4>
          <p>
            You agree to provide accurate, truthful, and authentic institutional information during registration. Student accounts require a valid 9-digit MAHE Learner ID verified against official university databases.
          </p>

          <h4 style={{ fontSize: "13px", fontWeight: 800, color: "#0F172A", margin: "12px 0 4px 0" }}>3. Community Standards & Code of Conduct</h4>
          <p>
            Users must maintain respectful, constructive dialogue across all Student Community feeds. The following behaviors are strictly prohibited:
          </p>
          <ul style={{ paddingLeft: "18px", margin: "4px 0" }}>
            <li>Harassment, targeted abuse, hate speech, or threatening communications.</li>
            <li>Explicit sexual content, exploitation, or sexually inappropriate material.</li>
            <li>Promotion or facilitation of illegal activity, illegal substance abuse, or unauthorized trade.</li>
            <li>Spam, promotional advertising, or impersonation of campus officials or students.</li>
            <li>Deliberate dissemination of misinformation, fake circulars, or vote manipulation.</li>
            <li>Attempts to bypass automated content moderation or pre-publish filter systems.</li>
          </ul>

          <h4 style={{ fontSize: "13px", fontWeight: 800, color: "#0F172A", margin: "12px 0 4px 0" }}>4. Misuse of Platform & Security Vulnerabilities</h4>
          <p>
            Automated scraping, API abuse, unauthorized access attempts to System Administrator endpoints, or exploitation of platform vulnerabilities is illegal and strictly prohibited.
          </p>

          <h4 style={{ fontSize: "13px", fontWeight: 800, color: "#0F172A", margin: "12px 0 4px 0" }}>5. Moderation, Strikes & Account Suspension Policy</h4>
          <p>
            Platform administrators reserve the right to review flagged posts, issue warning strikes, quarantine violating content, and temporarily or permanently suspend accounts. 
            <strong> Serious violations (e.g. harassment, illegal activity, platform abuse) may result in immediate account suspension without prior warning.</strong> Standard community guideline infractions follow the 3-strike policy.
          </p>

          <h4 style={{ fontSize: "13px", fontWeight: 800, color: "#0F172A", margin: "12px 0 4px 0" }}>6. Privacy & Data Processing Notice</h4>
          <p>
            Account details, Learner IDs, and community interactions are stored securely to provide platform features, active learning consensus detection, and community safety moderation audit logs.
          </p>
        </div>

        {/* Footer */}
        <div style={{ paddingTop: "12px", borderTop: "1px solid #E2E8F0", textAlign: "right" }}>
          <button className="auth-submit-btn" onClick={onClose} style={{ padding: "8px 20px", fontSize: "12px" }}>
            I Understand & Close ✕
          </button>
        </div>
      </div>
    </div>
  );
}
