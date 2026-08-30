import React, { useState } from "react";
import { submitSystemFeedback } from "../api";

export default function FeedbackModal({ isOpen, onClose, initialCategory = "AI Answer", initialTargetId = null }) {
  const [category, setCategory] = useState(initialCategory);
  const [issueType, setIssueType] = useState("Information Outdated");
  const [message, setMessage] = useState("");
  const [suggestedInfo, setSuggestedInfo] = useState("");
  const [rating, setRating] = useState(5);
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    await submitSystemFeedback(category, `[${issueType}] ${message.trim()} (Suggested: ${suggestedInfo || 'N/A'})`, rating);
    setSubmitted(true);
    setTimeout(() => {
      setSubmitted(false);
      onClose();
    }, 2000);
  };

  const categories = [
    { id: "AI Answer", label: "🤖 AI Copilot Answer" },
    { id: "University Info", label: "🏛️ University Information" },
    { id: "Community Answer", label: "💬 Community Post/Answer" },
    { id: "Campus Services", label: "🏢 Campus Services" },
    { id: "Notifications", label: "🔔 Intelligent Notifications" },
    { id: "General Platform", label: "🌐 General Platform UX" },
  ];

  const issueTypes = [
    "Information Outdated",
    "Source Incorrect / Wrong Document",
    "Suggest Update",
    "Report Misinformation",
    "Thumbs Up 👍 (Helpful)",
    "Thumbs Down 👎 (Not Helpful)",
    "General Bug / Feedback",
  ];

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="rewards-modal-card fade-in" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "560px" }}>
        {/* Header */}
        <div className="rewards-modal-header">
          <div className="rewards-brand-group">
            <span className="rewards-trophy-icon">📣</span>
            <div>
              <h3 className="rewards-title">Submit Crowdsourced Feedback & Learning Signal</h3>
              <p className="rewards-subtitle">Help improve platform accuracy, flag outdated info, & train the AI model</p>
            </div>
          </div>
          <button className="auth-close-btn" onClick={onClose}>✕</button>
        </div>

        {submitted ? (
          <div className="alert-box success" style={{ margin: "20px 0" }}>
            ✓ Thank you! Your feedback has been logged as an Active Learning Signal.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="create-post-form" style={{ marginTop: "12px" }}>
            <label>Feedback Target / Area:</label>
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>

            <label>Feedback Type / Issue Flag:</label>
            <select value={issueType} onChange={(e) => setIssueType(e.target.value)}>
              {issueTypes.map((t, idx) => (
                <option key={idx} value={t}>
                  {t}
                </option>
              ))}
            </select>

            <label>Overall Satisfaction Rating:</label>
            <div className="rating-star-row">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  className={`star-btn ${star <= rating ? "active" : ""}`}
                  onClick={() => setRating(star)}
                >
                  ★
                </button>
              ))}
              <span className="rating-num-label">{rating} / 5 Stars</span>
            </div>

            <label>Details / Feedback Description:</label>
            <textarea
              rows={3}
              placeholder="e.g. The exam date mentioned in the answer was updated by MAHE circular..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              required
            />

            <label>Suggest Correct Information (Optional):</label>
            <input
              type="text"
              placeholder="e.g. Mid-sem starts March 16 instead of March 12"
              value={suggestedInfo}
              onChange={(e) => setSuggestedInfo(e.target.value)}
            />

            <button type="submit" className="post-submit-btn">
              Submit Learning Signal 🚀
            </button>
          </form>
        )}

        <div className="inspector-footer" style={{ marginTop: "12px" }}>
          <span className="footer-note">MIT CampusOS Active Learning Pipeline • Feedback directly trains vector RAG weighting</span>
        </div>
      </div>
    </div>
  );
}
