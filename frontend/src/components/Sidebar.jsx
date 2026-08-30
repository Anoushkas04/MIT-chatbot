const ROLE_META = {
  student:     { icon: "🎓", color: "#2563EB", label: "Current Student" },
  prospective: { icon: "🌟", color: "#0284C7", label: "Prospective Student" },
  faculty:     { icon: "👨‍🏫", color: "#0891B2", label: "Faculty Member" },
};

export default function Sidebar({
  open,
  onClose,
  t,
  chatHistory,
  role,
  onNewChat,
  language,
  setLanguage,
  languageOptions,
  onChangeRole,
}) {
  const meta = ROLE_META[role] || ROLE_META.student;

  return (
    <>
      {/* Overlay */}
      <div
        className={`sidebar-overlay ${open ? "visible" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <aside
        className={`sidebar ${open ? "open" : ""}`}
        aria-label="Navigation sidebar"
        aria-hidden={!open}
      >
        <div className="sidebar-inner">
          {/* Header */}
          <div className="sidebar-header">
            <div className="wordmark" aria-label="MIT Manipal AI">
              <div className="wordmark-badge">MIT</div>
              <span className="wordmark-text">Manipal</span>
              <span className="wordmark-sub">AI</span>
            </div>
            <button
              className="icon-btn"
              onClick={onClose}
              aria-label="Close sidebar"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          {/* Active Role */}
          <div className="sidebar-role">
            <span className="sidebar-role-icon">{meta.icon}</span>
            <div className="sidebar-role-info">
              <span className="sidebar-role-label">Active role</span>
              <span className="sidebar-role-name">{meta.label}</span>
            </div>
            <button
              className="sidebar-role-change"
              onClick={onChangeRole}
              aria-label="Change role"
            >
              Switch
            </button>
          </div>

          {/* New chat */}
          <button
            className="new-chat-btn"
            onClick={() => { onNewChat(); onClose(); }}
            aria-label="Start new chat"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" width="15" height="15">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            {t.newChat}
          </button>

          {/* History */}
          <div className="sidebar-section">
            <div className="sidebar-section-label">{t.history}</div>
            <nav className="sidebar-history-list" aria-label="Chat history">
              {chatHistory.map((chat) => (
                <div key={chat.id} className="history-item" role="button" tabIndex={0}>
                  <div className="history-icon" aria-hidden="true">
                    {ROLE_META[chat.role]?.icon || "💬"}
                  </div>
                  <div className="history-text">
                    <div className="history-title">{chat.title}</div>
                    <div className="history-time">{chat.time}</div>
                  </div>
                </div>
              ))}
            </nav>
          </div>

          {/* Settings */}
          <div className="sidebar-settings">
            <div className="sidebar-section-label">{t.settings}</div>

            <div className="settings-row">
              <span className="settings-label">{t.language}</span>
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
        </div>
      </aside>
    </>
  );
}
