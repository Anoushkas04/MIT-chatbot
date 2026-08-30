import React, { useState } from "react";

export default function KnowledgeLoopDiagram() {
  const [selectedStep, setSelectedStep] = useState(1);

  const loopSteps = [
    { step: 1, title: "Official University Data", icon: "📄", metric: "6 PDFs/CSVs", color: "#16A34A", desc: "Academic Calendars, Cutoff ranks, Faculty cabins & syllabi from MAHE." },
    { step: 2, title: "Knowledge Base", icon: "📚", metric: "5,420 Chunks", color: "#2563EB", desc: "Text-embedding-004 vector embeddings stored in FAISS vector index." },
    { step: 3, title: "RAG Engine", icon: "🔍", metric: "98.4% Precision", color: "#7C3AED", desc: "Hybrid semantic vector retrieval matching context to query." },
    { step: 4, title: "AI Assistant", icon: "🤖", metric: "Gemini 2.0 Flash", color: "#0284C7", desc: "Persona-grounded conversational copilot delivering grounded answers." },
    { step: 5, title: "User Interaction", icon: "👤", metric: "1,420 Queries", color: "#059669", desc: "Multi-stakeholder interactions (Student, Faculty, Parent, Admin)." },
    { step: 6, title: "Feedback Signals", icon: "📣", metric: "240 Signals", color: "#EA580C", desc: "👍/👎 Ratings, Outdated Flags, and User-suggested updates." },
    { step: 7, title: "Student Community", icon: "💬", metric: "42 Discussions", color: "#D97706", desc: "Reddit-style community posts & Q&A across 11 campus channels." },
    { step: 8, title: "Crowdsourced Knowledge", icon: "🟡", metric: "83 Peer Answers", color: "#CA8A04", desc: "High-upvoted student responses & peer-verified campus hacks." },
    { step: 9, title: "Knowledge Validation", icon: "⚖️", metric: "12 Candidates", color: "#DC2626", desc: "7-State Verification Pipeline & Active Learning Engine vetting facts." },
    { step: 10, title: "Knowledge Base Update", icon: "🔄", metric: "8 Re-Indexes", color: "#2563EB", desc: "Approved community consensus re-indexed into FAISS vector store." },
    { step: 11, title: "Improved AI", icon: "🚀", metric: "Self-Evolving", color: "#16A34A", desc: "AI Copilot updated with verified student wisdom + official data." },
  ];

  const current = loopSteps.find((s) => s.step === selectedStep) || loopSteps[0];

  return (
    <div className="knowledge-loop-container fade-in">
      <div className="loop-header-row">
        <div>
          <h3 className="loop-title">♾️ Central 11-Stage Closed-Loop Knowledge Architecture</h3>
          <p className="loop-subtitle">Official Data → Knowledge Base → RAG → AI → User → Feedback → Community → Validation → Vector Re-Index → Improved AI</p>
        </div>
        <span className="loop-status-pill">🔄 Active Continuous Flywheel</span>
      </div>

      {/* Visual Flowchart Grid */}
      <div className="loop-flow-grid">
        {loopSteps.map((s, idx) => (
          <React.Fragment key={s.step}>
            <div
              className={`loop-node-card ${selectedStep === s.step ? "active" : ""}`}
              onClick={() => setSelectedStep(s.step)}
              style={{ borderColor: selectedStep === s.step ? s.color : "#E2E8F0" }}
            >
              <div className="node-step-num" style={{ background: s.color }}>{s.step}</div>
              <span className="node-icon">{s.icon}</span>
              <span className="node-title">{s.title}</span>
              <span className="node-metric">{s.metric}</span>
            </div>
            {idx < loopSteps.length - 1 && <span className="loop-arrow">↓</span>}
          </React.Fragment>
        ))}
      </div>

      {/* Step Detail Card */}
      <div className="loop-detail-card" style={{ borderLeft: `4px solid ${current.color}` }}>
        <div className="detail-head">
          <span className="detail-icon">{current.icon}</span>
          <div>
            <h4 className="detail-title">Stage {current.step}: {current.title}</h4>
            <span className="detail-metric-badge" style={{ background: `${current.color}15`, color: current.color }}>
              Live Metric: {current.metric}
            </span>
          </div>
        </div>
        <p className="detail-desc">{current.desc}</p>
      </div>
    </div>
  );
}
