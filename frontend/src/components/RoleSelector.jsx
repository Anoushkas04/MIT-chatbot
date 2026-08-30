const ROLE_CONFIG = {
  student: {
    icon: "🎓",
    title: "Current Student",
    desc: "Timetables, placements, exams & campus services",
    modifier: "rs-card--student",
  },
  prospective: {
    icon: "🌟",
    title: "Prospective Student",
    desc: "Admissions, fees, eligibility & campus tour",
    modifier: "rs-card--prospective",
  },
  faculty: {
    icon: "👨‍🏫",
    title: "Faculty Member",
    desc: "Courses, research grants & admin resources",
    modifier: "rs-card--faculty",
  },
};

const FEATURES = [
  { icon: "🧠", label: "Context-Aware" },
  { icon: "🌐", label: "Multilingual" },
  { icon: "⚡", label: "RAG-Powered" },
  { icon: "🔒", label: "Secure" },
  { icon: "📊", label: "Real-time Data" },
];

export default function RoleSelector({ t, onSelect, language, setLanguage, languageOptions }) {
  return (
    <div className="rs-root">
      <div className="rs-container">
        {/* Top bar */}
        <div className="rs-topbar">
          <div className="wordmark" aria-label="MIT Manipal AI Assistant">
            <div className="wordmark-badge" aria-hidden="true">MIT</div>
            <span className="wordmark-text">Manipal</span>
            <span className="wordmark-sub">AI</span>
          </div>
          <div className="rs-topbar-actions">
            <select
              className="lang-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              aria-label="Select language"
            >
              {languageOptions.map((l) => (
                <option key={l.code} value={l.code}>{l.flag} {l.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Hero */}
        <div className="rs-hero">
          <div className="rs-eyebrow" role="note">
            <span className="rs-eyebrow-dot" aria-hidden="true" />
            AI · RAG · NLP · Multilingual
          </div>
          <h1 className="rs-title">
            Your intelligent<br />
            <span className="rs-title-gradient">{t.appName}</span>
          </h1>
          <p className="rs-subtitle">{t.welcomeSubtitle}</p>
        </div>

        {/* Role cards */}
        <div role="group" aria-labelledby="role-prompt-label" style={{ width: "100%", display: "flex", flexDirection: "column", gap: "var(--sp-3)" }}>
          <div className="rs-label" id="role-prompt-label">{t.selectRole}</div>
          <div className="rs-cards" role="list">
            {Object.entries(ROLE_CONFIG).map(([key, cfg]) => (
              <button
                key={key}
                className={`rs-card ${cfg.modifier}`}
                onClick={() => onSelect(key)}
                aria-label={`Select role: ${cfg.title}`}
                role="listitem"
              >
                <div className="rs-card-icon" aria-hidden="true">{cfg.icon}</div>
                <div className="rs-card-title">{t.roles[key]}</div>
                <div className="rs-card-desc">{cfg.desc}</div>
                <div className="rs-card-arrow" aria-hidden="true">→</div>
              </button>
            ))}
          </div>
        </div>

        {/* Features */}
        <div className="rs-features" role="list" aria-label="Features">
          {FEATURES.map((f) => (
            <span key={f.label} className="rs-feat" role="listitem">
              <span className="rs-feat-icon" aria-hidden="true">{f.icon}</span>
              {f.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
