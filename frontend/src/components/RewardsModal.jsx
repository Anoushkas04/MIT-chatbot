import React, { useState, useEffect } from "react";
import { fetchUserRewards } from "../api";

export default function RewardsModal({ isOpen, onClose, token }) {
  const [activeTab, setActiveTab] = useState("badges"); // "badges" | "history"
  const [rewardsData, setRewardsData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadRewards();
    }
  }, [isOpen, token]);

  const loadRewards = async () => {
    setLoading(true);
    try {
      const data = await fetchUserRewards(token);
      setRewardsData(data);
    } catch (err) {
      console.warn("Failed to load rewards:", err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const userBadges = rewardsData?.badges || [];
  const activityLog = rewardsData?.activity_log || [];

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="rewards-modal-card fade-in" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "520px" }}>
        {/* Header Banner */}
        <div className="rewards-modal-header">
          <div className="rewards-brand-group">
            <span className="rewards-trophy-icon">🏆</span>
            <div>
              <h3 className="rewards-title">Student Reputation & Badges Portfolio</h3>
              <p className="rewards-subtitle">Recognizing constructive campus contributions & peer knowledge sharing</p>
            </div>
          </div>
          <button className="auth-close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Score Summary Banner */}
        <div className="score-summary-banner">
          <div className="score-main">
            <span className="score-num">{rewardsData?.campus_points || 0}</span>
            <span className="score-unit">Campus Points</span>
          </div>
          <div className="score-badges-summary">
            <span className="score-rank-tag">Rank: {rewardsData?.rank || "Member"}</span>
            <span className="score-unlocked-tag">
              {userBadges.filter((b) => b.unlocked).length} Badges Unlocked
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="auth-tabs" style={{ marginTop: "12px" }}>
          <button
            className={`auth-tab ${activeTab === "badges" ? "active" : ""}`}
            onClick={() => setActiveTab("badges")}
          >
            🏅 Earned Badges Portfolio ({userBadges.filter((b) => b.unlocked).length})
          </button>
          <button
            className={`auth-tab ${activeTab === "history" ? "active" : ""}`}
            onClick={() => setActiveTab("history")}
          >
            📜 Points Activity History
          </button>
        </div>

        {/* Badges Grid View */}
        {activeTab === "badges" && (
          <div className="badges-grid-container" style={{ marginTop: "12px" }}>
            {userBadges.length > 0 ? (
              userBadges.map((badge) => (
                <div key={badge.id} className={`badge-card ${badge.unlocked ? "unlocked" : "locked"}`}>
                  <div className="badge-card-header">
                    <span className="badge-icon-lg">{badge.icon || "🏆"}</span>
                    <span className={`badge-status-pill ${badge.unlocked ? "unlocked" : "locked"}`}>
                      {badge.unlocked ? "Unlocked ✓" : "Locked 🔒"}
                    </span>
                  </div>
                  <h4 className="badge-name">{badge.name}</h4>
                  <p className="badge-desc">{badge.description}</p>
                </div>
              ))
            ) : (
              <div style={{ textAlign: "center", padding: "30px", color: "#64748B", fontSize: "12px" }}>
                No unlocked badges yet. Earn campus points by asking questions and providing peer answers!
              </div>
            )}
          </div>
        )}

        {/* Activity Log View */}
        {activeTab === "history" && (
          <div className="points-history-list" style={{ marginTop: "12px" }}>
            {activityLog.length > 0 ? (
              activityLog.map((log) => (
                <div key={log.id} className="history-log-row">
                  <span className="log-icon">{log.icon || "✓"}</span>
                  <div className="log-content">
                    <span className="log-action">{log.action}</span>
                    <span className="log-time">{log.time}</span>
                  </div>
                  <span className="log-points-pill">{log.points}</span>
                </div>
              ))
            ) : (
              <div style={{ textAlign: "center", padding: "30px", color: "#64748B", fontSize: "12px" }}>
                No points activity logged yet.
              </div>
            )}
          </div>
        )}

        {/* Modal Footer */}
        <div className="inspector-footer" style={{ marginTop: "16px" }}>
          <span className="footer-note">MIT CampusOS Reputation System • Built for Academic & Peer Excellence</span>
        </div>
      </div>
    </div>
  );
}
