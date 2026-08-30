import React, { useState } from "react";

export default function Navbar({
  activeTab,
  setActiveTab,
  role,
  setRole,
  language,
  setLanguage,
  languageOptions,
  copilotOpen,
  setCopilotOpen,
  user,
  onOpenAuthModal,
  onLogout,
  unreadNotifCount,
  onOpenNotifDrawer,
  onOpenRewardsModal,
  onOpenFeedbackModal,
  onOpenSearchModal,
}) {
  const [profileOpen, setProfileOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="platform-nav">
      <div className="nav-container">
        {/* Left: Brand Identity & Mobile Hamburger Toggle */}
        <div className="nav-brand">
          <button
            className="mobile-hamburger-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle mobile menu"
          >
            ☰
          </button>
          <div className="brand-logo" onClick={() => setActiveTab("student_corner")}>
            <span className="brand-badge">MAHE</span>
            <span className="brand-title">MIT CampusOS</span>
          </div>
          <div className="system-status-pill" title="University Digital Operating Platform">
            <span className="status-dot"></span>
            <span className="status-text">University Platform Live</span>
          </div>
        </div>

        {/* Center: Stakeholder Workspace Navigation */}
        <nav className="nav-tabs" aria-label="Stakeholder Workspaces">
          <button
            className={`nav-tab ${activeTab === "student_corner" ? "active" : ""}`}
            onClick={() => {
              setActiveTab("student_corner");
              setRole("student");
            }}
          >
            <span className="tab-icon">🎓</span>
            <span className="tab-label">Student Corner</span>
          </button>

          {/* Faculty Workspace Tab (Visible if Faculty user) */}
          {(user?.role === "faculty" || activeTab === "faculty_portal") && (
            <button
              className={`nav-tab ${activeTab === "faculty_portal" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("faculty_portal");
                setRole("faculty");
              }}
            >
              <span className="tab-icon">👨‍🏫</span>
              <span className="tab-label">Faculty Workspace</span>
            </button>
          )}

          <button
            className={`nav-tab ${activeTab === "parent_hub" ? "active" : ""}`}
            onClick={() => {
              setActiveTab("parent_hub");
              setRole("parent");
            }}
          >
            <span className="tab-icon">🏛️</span>
            <span className="tab-label">Campus Info</span>
          </button>

          {/* Admin Console Tab (Strictly for System Administrators) */}
          {user?.role === "admin" && (
            <button
              className={`nav-tab ${activeTab === "admin_portal" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("admin_portal");
                setRole("admin");
              }}
            >
              <span className="tab-icon">👑</span>
              <span className="tab-label">Admin Console</span>
            </button>
          )}
        </nav>

        {/* Right: Actions, Notifications, User Menu & Copilot Trigger */}
        <div className="nav-actions">
          {/* Global Search Bar */}
          <div className="navbar-search-bar" onClick={() => onOpenSearchModal && onOpenSearchModal()}>
            <span className="search-bar-icon">🔍</span>
            <span className="search-bar-text">Search university docs, posts...</span>
            <span className="search-shortcut-badge">⌘K</span>
          </div>

          {/* Notifications Bell */}
          <button
            className="nav-icon-btn"
            onClick={onOpenNotifDrawer}
            title="Notifications & Alerts"
          >
            <span className="bell-icon">🔔</span>
            {unreadNotifCount > 0 && (
              <span className="notif-badge">{unreadNotifCount}</span>
            )}
          </button>

          {/* Language Selector */}
          <select
            className="lang-select-nav"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            aria-label="Select platform language"
          >
            {languageOptions.map((l) => (
              <option key={l.code} value={l.code}>
                {l.flag} {l.label}
              </option>
            ))}
          </select>

          {/* AI Chat Toggle */}
          <button
            className={`copilot-trigger-btn ${copilotOpen ? "active" : ""}`}
            onClick={() => setCopilotOpen(!copilotOpen)}
            title="Toggle AI Campus Assistant"
          >
            <span className="copilot-icon">💬</span>
            <span className="copilot-btn-text">{copilotOpen ? "Close AI" : "Ask AI"}</span>
          </button>

          {/* Universal Crowdsourced Feedback Trigger */}
          <button
            className="feedback-navbar-btn"
            onClick={() => onOpenFeedbackModal && onOpenFeedbackModal("General Platform", "General Bug / Feedback")}
            title="Submit Crowdsourced Feedback & Learning Signal"
          >
            <span className="feedback-icon">📣</span>
            <span className="feedback-btn-text">Feedback</span>
          </button>

          {/* User Profile / Auth State */}
          {user ? (
            <div className="user-profile-menu-wrap">
              <button
                className="user-profile-btn"
                onClick={() => setProfileOpen(!profileOpen)}
              >
                <span className="u-avatar">{user.avatar_icon || "👤"}</span>
                <div className="u-name-group">
                  <span className="u-name">{user.name}</span>
                  <span className="u-role-pill">{user.role.toUpperCase()}</span>
                </div>
                {user.role === "student" && (
                  <span className="u-rewards-badge" title="Campus Gamified Points">
                    🏆 {user.rewards_points || 0} pts
                  </span>
                )}
              </button>

              {profileOpen && (
                <div className="profile-dropdown-menu">
                  <div className="dropdown-user-header">
                    <span className="dropdown-name">{user.name}</span>
                    <span className="dropdown-email">{user.email}</span>
                  </div>
                  <div className="dropdown-divider"></div>
                  {user.role === "admin" && (
                    <button
                      className="dropdown-item"
                      onClick={() => {
                        setActiveTab("admin_portal");
                        setRole("admin");
                        setProfileOpen(false);
                      }}
                    >
                      👑 Admin Dashboard
                    </button>
                  )}
                  <button className="dropdown-item logout" onClick={() => { onLogout(); setProfileOpen(false); }}>
                    🚪 Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button className="auth-login-trigger-btn" onClick={onOpenAuthModal}>
              🔐 <span className="auth-btn-text">Sign In / Demo</span>
            </button>
          )}
        </div>
      </div>

      {/* Mobile Drawer Navigation Menu */}
      {mobileMenuOpen && (
        <div className="mobile-nav-drawer-overlay fade-in" onClick={() => setMobileMenuOpen(false)}>
          <div className="mobile-nav-drawer-content" onClick={(e) => e.stopPropagation()}>
            <div className="mobile-nav-header">
              <span className="mobile-nav-title">MIT CampusOS Menu</span>
              <button className="modal-close-btn" onClick={() => setMobileMenuOpen(false)}>✕</button>
            </div>

            <div className="mobile-nav-body">
              <button
                className={`mobile-nav-item ${activeTab === "student_corner" ? "active" : ""}`}
                onClick={() => {
                  setActiveTab("student_corner");
                  setRole("student");
                  setMobileMenuOpen(false);
                }}
              >
                <span>🎓</span> Student Corner
              </button>

              {(user?.role === "faculty" || activeTab === "faculty_portal") && (
                <button
                  className={`mobile-nav-item ${activeTab === "faculty_portal" ? "active" : ""}`}
                  onClick={() => {
                    setActiveTab("faculty_portal");
                    setRole("faculty");
                    setMobileMenuOpen(false);
                  }}
                >
                  <span>👨‍🏫</span> Faculty Workspace
                </button>
              )}

              <button
                className={`mobile-nav-item ${activeTab === "parent_hub" ? "active" : ""}`}
                onClick={() => {
                  setActiveTab("parent_hub");
                  setRole("parent");
                  setMobileMenuOpen(false);
                }}
              >
                <span>🏛️</span> Campus Info
              </button>

              {user?.role === "admin" && (
                <button
                  className={`mobile-nav-item ${activeTab === "admin_portal" ? "active" : ""}`}
                  onClick={() => {
                    setActiveTab("admin_portal");
                    setRole("admin");
                    setMobileMenuOpen(false);
                  }}
                >
                  <span>👑</span> Admin Console
                </button>
              )}

              <div className="mobile-nav-divider"></div>

              <button
                className="mobile-nav-item"
                onClick={() => {
                  setCopilotOpen(true);
                  setMobileMenuOpen(false);
                }}
              >
                <span>🤖</span> Open AI Copilot
              </button>

              <button
                className="mobile-nav-item"
                onClick={() => {
                  onOpenSearchModal && onOpenSearchModal();
                  setMobileMenuOpen(false);
                }}
              >
                <span>🔍</span> Global Search
              </button>

              <button
                className="mobile-nav-item"
                onClick={() => {
                  onOpenFeedbackModal && onOpenFeedbackModal();
                  setMobileMenuOpen(false);
                }}
              >
                <span>📣</span> Submit Feedback
              </button>

              <div className="mobile-nav-divider"></div>

              <select
                className="mobile-nav-lang-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                aria-label="Select platform language"
              >
                {languageOptions.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.flag} {l.label}
                  </option>
                ))}
              </select>

              {user ? (
                <button
                  className="mobile-nav-item logout"
                  onClick={() => {
                    onLogout();
                    setMobileMenuOpen(false);
                  }}
                >
                  <span>🚪</span> Sign Out
                </button>
              ) : (
                <button
                  className="mobile-nav-item"
                  onClick={() => {
                    onOpenAuthModal();
                    setMobileMenuOpen(false);
                  }}
                >
                  <span>🔐</span> Sign In / Demo
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

