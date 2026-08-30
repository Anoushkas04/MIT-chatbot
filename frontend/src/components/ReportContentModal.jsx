import React, { useState } from "react";

export default function ReportContentModal({ isOpen, onClose, targetTitle = "Community Post", onReportSubmitted }) {
  const [reason, setReason] = useState("Outdated Information");
  const [comments, setComments] = useState("");
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    if (onReportSubmitted) {
      onReportSubmitted({ reason, comments, targetTitle });
    }
    setTimeout(() => {
      setSubmitted(false);
      onClose();
    }, 1200);
  };

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="rewards-modal-card fade-in" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "480px", padding: "24px" }}>
        <div className="modal-header-row">
          <div className="modal-title-group">
            <span className="modal-title-icon">🚩</span>
            <div>
              <h3 className="modal-title-text">Report Post / Flag Misinformation</h3>
              <p className="modal-sub-text">Help administrators & community maintain verified accuracy</p>
            </div>
          </div>
          <button className="auth-close-btn" onClick={onClose}>✕</button>
        </div>

        {submitted ? (
          <div className="success-banner" style={{ marginTop: "16px", background: "#DCFCE7", color: "#15803D", padding: "16px", borderRadius: "12px", textAlign: "center", fontWeight: 700 }}>
            ✓ Report submitted for Admin & Moderator review. Thank you!
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div className="p-field">
              <label style={{ fontSize: "12px", fontWeight: 700, color: "#334155" }}>Reporting Target:</label>
              <div style={{ fontSize: "12px", fontWeight: 800, color: "#0F172A", background: "#F1F5F9", padding: "8px 12px", borderRadius: "8px" }}>
                "{targetTitle}"
              </div>
            </div>

            <div className="p-field">
              <label style={{ fontSize: "12px", fontWeight: 700, color: "#334155" }}>Reason for Flagging:</label>
              <select
                style={{ width: "100%", padding: "8px 12px", borderRadius: "10px", border: "1px solid #CBD5E1", fontSize: "13px" }}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              >
                <option value="Outdated Information">⚠️ Information Outdated (Rules/Timings Changed)</option>
                <option value="Flag Misinformation">❌ Misinformation / Factually Incorrect</option>
                <option value="Spam / Advertising">🚫 Spam, Self-Promotion, or Duplicates</option>
                <option value="Incorrect Source">📄 Incorrect Document Sourced</option>
                <option value="Harassment / Abusive">🛡️ Harassment or Abusive Content</option>
              </select>
            </div>

            <div className="p-field">
              <label style={{ fontSize: "12px", fontWeight: 700, color: "#334155" }}>Additional Context / Suggested Correct Facts:</label>
              <textarea
                rows="3"
                placeholder="Explain what is incorrect or outdated..."
                style={{ width: "100%", padding: "8px 12px", borderRadius: "10px", border: "1px solid #CBD5E1", fontSize: "12px" }}
                value={comments}
                onChange={(e) => setComments(e.target.value)}
              />
            </div>

            <div className="modal-actions-row" style={{ marginTop: "8px", display: "flex", justifyContent: "flex-end", gap: "8px" }}>
              <button type="button" className="auth-tab" onClick={onClose}>Cancel</button>
              <button type="submit" className="action-btn report-flag-btn" style={{ padding: "8px 16px" }}>
                Submit Report 🚩
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
