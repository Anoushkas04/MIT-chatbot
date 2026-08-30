import React, { useState, useEffect } from "react";
import { createCommunityPost } from "../api";

export default function AICommunityHandoffModal({ isOpen, onClose, initialPrompt = "", onPostCreated }) {
  const [title, setTitle] = useState(initialPrompt);
  const [category, setCategory] = useState("Academics");
  const [subCommunity, setSubCommunity] = useState("General");
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setTitle(initialPrompt || "");
      setContent(`The AI Copilot couldn't find an official document answer for: "${initialPrompt}". Asking the MIT Manipal student community for peer insights!`);
      setSuccess(false);
      setErrorMsg(null);
    }
  }, [isOpen, initialPrompt]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    setErrorMsg(null);

    const newPost = {
      title,
      content,
      category,
      sub_community: subCommunity,
      author: "Student Community Member",
      author_role: "student",
      author_avatar: "🎓",
    };

    try {
      const res = await createCommunityPost(newPost);
      setSubmitting(false);
      setSuccess(true);

      if (onPostCreated) {
        onPostCreated(res || newPost);
        window.dispatchEvent(new CustomEvent("community_post_created"));
      }

      setTimeout(() => {
        onClose();
      }, 1200);
    } catch (err) {
      setSubmitting(false);
      setErrorMsg(err.message || "Your post could not be submitted. The selected category does not appear to match your question.");
    }
  };

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="rewards-modal-card fade-in" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "560px", padding: "24px" }}>
        <div className="modal-header-row">
          <div className="modal-title-group">
            <span className="modal-title-icon">🔀</span>
            <div>
              <h3 className="modal-title-text">AI → Community Knowledge Handoff</h3>
              <p className="modal-sub-text">Convert your query into a live Student Corner community post</p>
            </div>
          </div>
          <button className="auth-close-btn" onClick={onClose}>✕</button>
        </div>

        {errorMsg && (
          <div className="category-mismatch-toast fade-in" style={{ marginTop: "12px", background: "#FFFBEB", borderLeft: "4px solid #F59E0B", color: "#92400E", padding: "12px 14px", borderRadius: "10px", fontSize: "12px", fontWeight: 600 }}>
            <strong style={{ fontSize: "13px" }}>⚠️ Your post could not be submitted.</strong>
            <p style={{ margin: "4px 0 0 0" }}>{errorMsg}</p>
          </div>
        )}

        {success ? (
          <div className="success-banner" style={{ marginTop: "16px", background: "#DCFCE7", color: "#15803D", padding: "16px", borderRadius: "12px", textAlign: "center", fontWeight: 700 }}>
            ✓ Successfully published to Student Corner! Redirecting...
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div className="p-field">
              <label style={{ fontSize: "12px", fontWeight: 700, color: "#334155" }}>Question Title:</label>
              <input
                type="text"
                className="search-modal-input"
                style={{ border: "1px solid #CBD5E1", borderRadius: "10px", padding: "8px 12px", fontSize: "13px" }}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
              <div className="p-field">
                <label style={{ fontSize: "12px", fontWeight: 700, color: "#334155" }}>Category:</label>
                <select
                  style={{ width: "100%", padding: "8px", borderRadius: "10px", border: "1px solid #CBD5E1" }}
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  <option value="Academics">Academics</option>
                  <option value="Hostel & Mess">Hostel & Mess</option>
                  <option value="Campus Life">Campus Life</option>
                  <option value="Clubs & Events">Clubs & Events</option>
                  <option value="Facilities & Printing">Facilities & Printing</option>
                </select>
              </div>

              <div className="p-field">
                <label style={{ fontSize: "12px", fontWeight: 700, color: "#334155" }}>Sub-Community:</label>
                <select
                  style={{ width: "100%", padding: "8px", borderRadius: "10px", border: "1px solid #CBD5E1" }}
                  value={subCommunity}
                  onChange={(e) => setSubCommunity(e.target.value)}
                >
                  <option value="General">General</option>
                  <option value="Block 13 & 16">Block 13 & 16</option>
                  <option value="AB5 Students">AB5 Students</option>
                  <option value="Freshman Advice">Freshman Advice</option>
                </select>
              </div>
            </div>

            <div className="p-field">
              <label style={{ fontSize: "12px", fontWeight: 700, color: "#334155" }}>Context / Details:</label>
              <textarea
                rows="3"
                style={{ width: "100%", padding: "8px 12px", borderRadius: "10px", border: "1px solid #CBD5E1", fontSize: "12px" }}
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
            </div>

            <div className="modal-actions-row" style={{ marginTop: "8px", display: "flex", justifyContent: "flex-end", gap: "8px" }}>
              <button type="button" className="auth-tab" onClick={onClose}>Cancel</button>
              <button type="submit" className="action-btn approve" disabled={submitting} style={{ padding: "8px 16px" }}>
                {submitting ? "Publishing..." : "Post to Student Corner 💬"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
