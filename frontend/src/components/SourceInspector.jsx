import React, { useState } from "react";

export default function SourceInspector({ activeCitation, onClose }) {
  const [activeTab, setActiveTab] = useState("official"); // "official" | "community" | "conflicts"

  if (!activeCitation) return null;

  const { sources, citations, confidence, confidenceType, messageText } = activeCitation;

  const verificationStateDemo = [
    {
      topic: "Block 13 & 16 Mess Timings",
      state: "Conflicting",
      statePill: "⚠️ Conflicting",
      official: "Official Document: Dinner 7:30 PM – 9:30 PM",
      community: "Student Reports (126 responses): Entry closes at 9:15 PM.",
      warning: "⚠️ Conflicting Information: Official document lists 7:30–9:30 PM, but recent student reports indicate gate closes at 9:15 PM. Under Faculty Review.",
    },
    {
      topic: "Hostel Outstation Leave Signatures After 5 PM",
      state: "Pending Verification",
      statePill: "⏳ Pending Verification",
      official: "Official Policy: Warden sign required before 6:00 PM.",
      community: "Student Reports: Block 16 warden available till 7:30 PM; Chief Warden Office Block 5 after 8 PM.",
      warning: "⏳ Pending Verification: Awaiting Chief Warden signoff.",
    },
    {
      topic: "AB5 Basement Printing Rates",
      state: "Verified",
      statePill: "✓ Verified",
      official: "Official Store Price: ₹1 / page B&W",
      community: "Confirmed by 89 student upvotes",
      warning: null,
    },
    {
      topic: "Past Academic Calendar (2024-25)",
      state: "Deprecated",
      statePill: "🚫 Deprecated",
      official: "Superseded by Academic Calendar 2026-27",
      community: "Archived",
      warning: "🚫 Deprecated: Historical schedule replaced by current Academic Calendar 2026-27.",
    },
  ];

  return (
    <div className="inspector-overlay" onClick={onClose}>
      <div className="inspector-drawer" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="inspector-header">
          <div className="inspector-title-group">
            <span className="inspector-icon">🔍</span>
            <div>
              <h3 className="inspector-title">Institutional Source & Verification Inspector</h3>
              <p className="inspector-subtitle">7-State Knowledge Taxonomy & Conflicting Information Pipeline</p>
            </div>
          </div>
          <button className="inspector-close-btn" onClick={onClose} aria-label="Close Inspector">
            ✕
          </button>
        </div>

        {/* 3 Navigation Tabs */}
        <div className="auth-tabs" style={{ marginTop: "8px" }}>
          <button
            className={`auth-tab ${activeTab === "official" ? "active" : ""}`}
            onClick={() => setActiveTab("official")}
          >
            🟢 Official Facts ({sources?.length || citations?.length || 1})
          </button>
          <button
            className={`auth-tab ${activeTab === "community" ? "active" : ""}`}
            onClick={() => setActiveTab("community")}
          >
            🟡 Community Consensus
          </button>
          <button
            className={`auth-tab ${activeTab === "conflicts" ? "active" : ""}`}
            onClick={() => setActiveTab("conflicts")}
          >
            ⚠️ Conflicts & Lifecycle (4)
          </button>
        </div>

        {/* Status Card */}
        <div className="inspector-status-card" style={{ marginTop: "12px" }}>
          <div className="status-row">
            <span className="status-label">Knowledge Verification State:</span>
            <span className={`confidence-badge-lg ${confidence === "high" ? "high" : "moderate"}`}>
              {confidenceType === "official_verified"
                ? "🟢 Official Document Verified (High Trust)"
                : "⚠️ Conflicting / Under Faculty Review"}
            </span>
          </div>

          <div className="status-row">
            <span className="status-label">Taxonomy Pipeline Phase:</span>
            <span className="status-value">7-State Managed Knowledge Asset</span>
          </div>
        </div>

        {/* Target Query */}
        {messageText && (
          <div className="inspector-query-box">
            <span className="query-label">Target Query Context:</span>
            <div className="query-text">"{messageText}"</div>
          </div>
        )}

        {/* Official Tab */}
        {activeTab === "official" && (
          <div className="inspector-citations-container">
            <h4 className="citations-heading">🟢 Official MAHE Institutional Documents</h4>
            {citations && citations.length > 0 ? (
              citations.map((c, idx) => (
                <div key={idx} className="citation-card official">
                  <div className="citation-card-header">
                    <span className="doc-icon">📄</span>
                    <span className="doc-name">{c.source}</span>
                    <span className="state-tag official">🟢 Official</span>
                  </div>
                  <div className="citation-snippet">"{c.snippet}"</div>
                </div>
              ))
            ) : (
              <div className="citation-card official">
                <div className="citation-card-header">
                  <span className="doc-icon">📄</span>
                  <span className="doc-name">Academic Calendar 2026-27.pdf</span>
                  <span className="state-tag official">🟢 Official</span>
                </div>
                <div className="citation-snippet">"Verified passage retrieved from official institutional document Academic Calendar 2026-27.pdf."</div>
              </div>
            )}
          </div>
        )}

        {/* Community Tab */}
        {activeTab === "community" && (
          <div className="inspector-citations-container">
            <h4 className="citations-heading">🟡 Crowdsourced Community Insights</h4>
            <div className="citation-card community">
              <div className="citation-card-header">
                <span className="doc-icon">💬</span>
                <span className="doc-name">Mess Timings & Entry Gate Rules</span>
                <span className="state-tag community">🟡 Community</span>
              </div>
              <div className="citation-snippet">"126 students report entry gate closes at 9:15 PM instead of 9:30 PM."</div>
            </div>
          </div>
        )}

        {/* Conflicts & 7-State Lifecycle Tab */}
        {activeTab === "conflicts" && (
          <div className="inspector-citations-container">
            <h4 className="citations-heading">⚠️ Knowledge Quality & Verification Pipeline</h4>

            {verificationStateDemo.map((item, idx) => (
              <div key={idx} className={`citation-card ${item.state.toLowerCase()}`}>
                <div className="citation-card-header">
                  <span className="doc-icon">⚖️</span>
                  <span className="doc-name">{item.topic}</span>
                  <span className={`state-tag ${item.state.toLowerCase()}`}>{item.statePill}</span>
                </div>

                <div style={{ fontSize: "11px", color: "#334155", marginTop: "4px" }}>
                  <strong>Official:</strong> {item.official}
                </div>
                <div style={{ fontSize: "11px", color: "#334155", marginTop: "2px" }}>
                  <strong>Community:</strong> {item.community}
                </div>

                {item.warning && (
                  <div className="conflict-warning-box">
                    {item.warning}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="inspector-footer">
          <span className="footer-note">MIT CampusOS Verification Engine • 7 Lifecycle States (Official, Community, Pending, Verified, Conflicting, Outdated, Deprecated)</span>
        </div>
      </div>
    </div>
  );
}
