import { useState, useEffect } from "react";
import {
  generateAIResponse,
  fetchCurrentUserProfile,
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  dismissNotification,
  dismissPopupNotification,
  dismissAllPopups,
} from "./api";
import { translations, languageOptions } from "./translations";
import Navbar from "./components/Navbar";
import StudentCorner from "./components/StudentCorner";
import FacultyPortal from "./components/FacultyPortal";
import ParentHub from "./components/ParentHub";
import AdminPortal from "./components/AdminPortal";
import ChatWindow from "./components/ChatWindow";
import SourceInspector from "./components/SourceInspector";
import AuthModal from "./components/AuthModal";
import NotificationsDrawer from "./components/NotificationsDrawer";
import NotificationToast from "./components/NotificationToast";
import RewardsModal from "./components/RewardsModal";
import FeedbackModal from "./components/FeedbackModal";
import GlobalSearchModal from "./components/GlobalSearchModal";
import AICommunityHandoffModal from "./components/AICommunityHandoffModal";
import ReportContentModal from "./components/ReportContentModal";
import Sidebar from "./components/Sidebar";
import "./App.css";

function App() {
  const [activeTab, setActiveTab] = useState("student_corner"); // "student_corner" | "faculty_portal" | "parent_hub" | "admin_portal"
  // Auth & User State
  const [token, setToken] = useState(() => localStorage.getItem("campus_token") || null);
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("campus_user");
    return saved ? JSON.parse(saved) : null;
  });
  const [role, setRole] = useState(() => (user?.role || "student"));
  const [language, setLanguage] = useState("en");

  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [rewardsModalOpen, setRewardsModalOpen] = useState(false);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [feedbackCategory, setFeedbackCategory] = useState("AI Answer");
  const [feedbackTargetId, setFeedbackTargetId] = useState(null);
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [handoffModalOpen, setHandoffModalOpen] = useState(false);
  const [handoffPrompt, setHandoffPrompt] = useState("");
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportTargetTitle, setReportTargetTitle] = useState("Community Post");

  // Sync session on mount if token exists
  useEffect(() => {
    if (token) {
      fetchCurrentUserProfile(token)
        .then((profile) => {
          if (profile) {
            setUser(profile);
            setRole(profile.role || "student");
            localStorage.setItem("campus_user", JSON.stringify(profile));
          } else {
            handleLogout();
          }
        })
        .catch(() => handleLogout());
    }
  }, [token]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearchModalOpen(true);
      }
    };
    const handleOpenHandoff = (e) => {
      setHandoffPrompt(e.detail?.prompt || "");
      setHandoffModalOpen(true);
    };
    const handleOpenReport = (e) => {
      setReportTargetTitle(e.detail?.title || "Community Post");
      setReportModalOpen(true);
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("open_handoff_modal", handleOpenHandoff);
    window.addEventListener("open_report_modal", handleOpenReport);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("open_handoff_modal", handleOpenHandoff);
      window.removeEventListener("open_report_modal", handleOpenReport);
    };
  }, []);

  const handleOpenFeedbackModal = (category = "AI Answer", targetId = null) => {
    setFeedbackCategory(category);
    setFeedbackTargetId(targetId);
    setFeedbackModalOpen(true);
  };

  // Personalization State
  const [department, setDepartment] = useState(() => (user?.department || "Computer Science & Engineering"));
  const [academicYear, setAcademicYear] = useState(() => (user?.academic_year || "3rd Year (2023-27)"));
  const [semester, setSemester] = useState(() => (user?.semester || "Even Semester (Jan - May)"));

  // Notifications State
  const [notifDrawerOpen, setNotifDrawerOpen] = useState(false);
  const [notificationsData, setNotificationsData] = useState({ unread_count: 0, notifications: [], popup_notification: null });

  // Load backend calendar notifications & set up 15s polling
  useEffect(() => {
    loadCalendarNotifications();
    const interval = setInterval(() => {
      loadCalendarNotifications();
    }, 15000);
    return () => clearInterval(interval);
  }, [user, role, department, academicYear]);

  const loadCalendarNotifications = async () => {
    const res = await fetchNotifications(user?.id || "guest", role, department, academicYear);
    if (res && res.notifications) {
      setNotificationsData(res);
    }
  };

  // Copilot Drawer & Inspection State
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [activeCitation, setActiveCitation] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Chat State
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const [chatHistory, setChatHistory] = useState([]);

  const t = translations[language] || translations.en;

  const handleLoginSuccess = (userData, userToken) => {
    setUser(userData);
    setToken(userToken);
    setRole(userData.role || "student");
    if (userData.department) setDepartment(userData.department);
    if (userData.academic_year) setAcademicYear(userData.academic_year);
    if (userData.semester) setSemester(userData.semester);

    localStorage.setItem("campus_token", userToken);
    localStorage.setItem("campus_user", JSON.stringify(userData));

    if (userData.role === "student") setActiveTab("student_corner");
    else if (userData.role === "faculty") setActiveTab("faculty_portal");
    else if (userData.role === "parent") setActiveTab("parent_hub");
    else if (userData.role === "admin") setActiveTab("admin_portal");
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("campus_token");
    localStorage.removeItem("campus_user");
  };

  const handleMarkAllRead = async () => {
    setNotificationsData((prev) => ({
      ...prev,
      unread_count: 0,
      notifications: (prev.notifications || []).map((n) => ({ ...n, read: true })),
    }));
    await markAllNotificationsRead(user?.id || "guest");
    loadCalendarNotifications();
  };

  const handleMarkSingleRead = async (stateId) => {
    setNotificationsData((prev) => ({
      ...prev,
      unread_count: Math.max(0, (prev.unread_count || 1) - 1),
      notifications: (prev.notifications || []).map((n) =>
        n.state_id === stateId ? { ...n, read: true } : n
      ),
    }));
    await markNotificationRead(stateId);
  };

  const handleDismissNotification = async (stateId) => {
    setNotificationsData((prev) => {
      const list = prev.notifications || [];
      const target = list.find((n) => n.state_id === stateId);
      const isUnread = target && !target.read;
      return {
        ...prev,
        unread_count: isUnread ? Math.max(0, (prev.unread_count || 1) - 1) : prev.unread_count,
        notifications: list.filter((n) => n.state_id !== stateId),
        popup_notification: prev.popup_notification?.state_id === stateId ? null : prev.popup_notification,
      };
    });
    await dismissNotification(stateId);
  };

  const handleDismissPopup = async (stateId) => {
    await dismissPopupNotification(stateId);
    setNotificationsData((prev) => ({ ...prev, popup_notification: null }));
    loadCalendarNotifications();
  };

  const handleOpenNotificationDrawer = async () => {
    setNotifDrawerOpen(true);
    setNotificationsData((prev) => ({ ...prev, popup_notification: null }));
    await dismissAllPopups(user?.id || "guest");
  };

  const handleSend = async (text) => {
    const messageText = (text || input).trim();
    if (!messageText || isTyping) return;

    if (!copilotOpen) setCopilotOpen(true);

    const userMsg = {
      id: Date.now(),
      role: "user",
      text: messageText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const response = await generateAIResponse(messageText, role, language, sessionId, {
        department,
        academicYear,
        semester,
      });

      const aiMsg = {
        id: Date.now() + 1,
        role: "assistant",
        text: response.text,
        sources: response.sources,
        citations: response.citations || [],
        confidence: response.confidence,
        confidenceType: response.confidenceType || (response.confidence === "high" ? "official_verified" : "community_grounded"),
        followups: response.followups || [],
        question_count: response.question_count ?? 0,
        response_count: response.response_count ?? 0,
        demand_count: response.demand_count ?? 0,
        sample_size: response.sample_size ?? 0,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error("API error:", err);
      const errorMsg = {
        id: Date.now() + 1,
        role: "assistant",
        text: "I'm experiencing connectivity issues with the local FastAPI backend. Please verify your backend server is active on `http://localhost:8000`.",
        sources: ["System Connection Handler"],
        citations: [],
        confidence: "moderate",
        confidenceType: "community_grounded",
        followups: ["Check FastAPI server status"],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handlePromptSelect = (promptText) => {
    setCopilotOpen(true);
    handleSend(promptText);
  };

  const handleClearChat = () => {
    if (messages.length > 0) {
      const firstMsg = messages.find((m) => m.role === "user");
      setChatHistory((prev) => [
        {
          id: Date.now(),
          title: firstMsg ? firstMsg.text.slice(0, 36) + (firstMsg.text.length > 36 ? "…" : "") : "New conversation",
          time: "Just now",
          role,
        },
        ...prev.slice(0, 5),
      ]);
    }
    setMessages([]);
  };

  return (
    <div className="platform-root">
      {/* Platform Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        role={role}
        setRole={setRole}
        language={language}
        setLanguage={setLanguage}
        languageOptions={languageOptions}
        copilotOpen={copilotOpen}
        setCopilotOpen={setCopilotOpen}
        user={user}
        onOpenAuthModal={() => setAuthModalOpen(true)}
        onLogout={handleLogout}
        unreadNotifCount={notificationsData.unread_count || 0}
        onOpenNotifDrawer={handleOpenNotificationDrawer}
        onOpenRewardsModal={() => setRewardsModalOpen(true)}
        onOpenFeedbackModal={handleOpenFeedbackModal}
        onOpenSearchModal={() => setSearchModalOpen(true)}
      />

      {/* Main Platform Body */}
      <main className="platform-body">
        {/* Persistent Left Sidebar Navigation */}
        <nav className="platform-sidebar" aria-label="Main navigation">
          <div className="sidebar-nav">
            <span className="sidebar-section-label">Workspaces</span>
            <button
              className={`sidebar-nav-item ${activeTab === "student_corner" ? "active" : ""}`}
              onClick={() => { setActiveTab("student_corner"); setRole("student"); }}
            >
              <span className="nav-item-icon">🎓</span>
              Student Corner
            </button>

            {(user?.role === "faculty" || activeTab === "faculty_portal") && (
              <button
                className={`sidebar-nav-item ${activeTab === "faculty_portal" ? "active" : ""}`}
                onClick={() => { setActiveTab("faculty_portal"); setRole("faculty"); }}
              >
                <span className="nav-item-icon">📋</span>
                Faculty Workspace
              </button>
            )}

            <button
              className={`sidebar-nav-item ${activeTab === "parent_hub" ? "active" : ""}`}
              onClick={() => { setActiveTab("parent_hub"); setRole("parent"); }}
            >
              <span className="nav-item-icon">🏛️</span>
              Campus Info
            </button>

            {user?.role === "admin" && (
              <button
                className={`sidebar-nav-item ${activeTab === "admin_portal" ? "active" : ""}`}
                onClick={() => { setActiveTab("admin_portal"); setRole("admin"); }}
              >
                <span className="nav-item-icon">⚙️</span>
                Admin Console
              </button>
            )}

            <div className="sidebar-divider" />
            <span className="sidebar-section-label">Tools</span>

            <button
              className={`sidebar-nav-item ${copilotOpen ? "active" : ""}`}
              onClick={() => setCopilotOpen(!copilotOpen)}
            >
              <span className="nav-item-icon">💬</span>
              {copilotOpen ? "Close AI Chat" : "Ask AI"}
            </button>
          </div>

          {user && (
            <div className="sidebar-footer">
              <div className="sidebar-user-block">
                <span style={{ fontSize: "18px" }}>{user.avatar_icon || "👤"}</span>
                <div>
                  <div className="sidebar-user-name">{user.name}</div>
                  <div className="sidebar-user-role">{user.role} · {department?.split(" ")[0] || "MIT"}</div>
                </div>
              </div>
            </div>
          )}
        </nav>

        {/* Stakeholder Workspace Panels */}
        <div className="workspace-wrapper">
          {activeTab === "student_corner" && (
            <StudentCorner
              onPromptSelect={handlePromptSelect}
              department={department}
              setDepartment={setDepartment}
              academicYear={academicYear}
              setAcademicYear={setAcademicYear}
              semester={semester}
              setSemester={setSemester}
              t={t}
              onOpenRewardsModal={() => setRewardsModalOpen(true)}
            />
          )}

          {activeTab === "faculty_portal" && (
            <FacultyPortal onPromptSelect={handlePromptSelect} />
          )}

          {activeTab === "parent_hub" && (
            <ParentHub onPromptSelect={handlePromptSelect} />
          )}

          {activeTab === "admin_portal" && (
            user?.role === "admin" ? (
              <AdminPortal token={token} />
            ) : (
              <div className="workspace-container fade-in" style={{ padding: "40px", textAlign: "center" }}>
                <div style={{ background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: "8px", padding: "32px", maxWidth: "480px", margin: "0 auto" }}>
                  <span style={{ fontSize: "32px" }}>🔒</span>
                  <h3 style={{ fontSize: "16px", fontWeight: 600, color: "#991B1B", marginTop: "12px" }}>
                    Admin access required
                  </h3>
                  <p style={{ fontSize: "13px", color: "#7F1D1D", marginTop: "8px", lineHeight: "1.5" }}>
                    You are logged in as <strong>{user?.role?.toUpperCase() || "STUDENT"}</strong>. The Admin Console is restricted to system administrators.
                  </p>
                  <button
                    className="auth-submit-btn"
                    onClick={() => { setActiveTab("student_corner"); setRole("student"); }}
                    style={{ marginTop: "16px" }}
                  >
                    Return to Student Corner
                  </button>
                </div>
              </div>
            )
          )}
        </div>

        {/* AI Copilot — inline right panel */}
        {copilotOpen && (
          <aside className="copilot-drawer-panel fade-in-right">
            <ChatWindow
              t={t}
              messages={messages}
              isTyping={isTyping}
              input={input}
              setInput={setInput}
              onSend={handleSend}
              role={role}
              language={language}
              setLanguage={setLanguage}
              languageOptions={languageOptions}
              onClearChat={handleClearChat}
              isDrawer={true}
              onCloseDrawer={() => setCopilotOpen(false)}
              onInspectCitation={(citation) => setActiveCitation(citation)}
              onOpenFeedback={handleOpenFeedbackModal}
              department={department}
              academicYear={academicYear}
              semester={semester}
            />
          </aside>
        )}
      </main>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onLoginSuccess={handleLoginSuccess}
      />

      {/* Notifications Drawer */}
      <NotificationsDrawer
        isOpen={notifDrawerOpen}
        onClose={() => setNotifDrawerOpen(false)}
        notifications={notificationsData.notifications}
        unreadCount={notificationsData.unread_count}
        onMarkAllRead={handleMarkAllRead}
        onMarkSingleRead={handleMarkSingleRead}
        onDismissNotification={handleDismissNotification}
      />

      {/* Real-time Time-Threshold Notification Toast Alert */}
      <NotificationToast
        notification={notificationsData.popup_notification}
        onOpenDrawer={handleOpenNotificationDrawer}
        onDismissPopup={handleDismissPopup}
        drawerOpen={notifDrawerOpen}
        copilotOpen={copilotOpen}
      />

      {/* Student Reputation & Badges Portfolio Modal */}
      <RewardsModal
        isOpen={rewardsModalOpen}
        onClose={() => setRewardsModalOpen(false)}
      />

      {/* Universal Crowdsourced Feedback Modal */}
      <FeedbackModal
        isOpen={feedbackModalOpen}
        onClose={() => setFeedbackModalOpen(false)}
        initialCategory={feedbackCategory}
        initialTargetId={feedbackTargetId}
      />

      {/* Global Intelligent Multi-Domain Search Modal */}
      <GlobalSearchModal
        isOpen={searchModalOpen}
        onClose={() => setSearchModalOpen(false)}
        onAskCopilot={(queryText) => {
          setCopilotOpen(true);
          handlePromptSelect(queryText);
        }}
      />

      {/* AI -> Community Handoff Modal */}
      <AICommunityHandoffModal
        isOpen={handoffModalOpen}
        onClose={() => setHandoffModalOpen(false)}
        initialPrompt={handoffPrompt}
        onPostCreated={() => {
          setActiveTab("student_corner");
        }}
      />

      {/* Community Content & Misinformation Report Modal */}
      <ReportContentModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        targetTitle={reportTargetTitle}
      />

      {/* Visual Source Inspector Modal */}
      {activeCitation && (
        <SourceInspector
          activeCitation={activeCitation}
          onClose={() => setActiveCitation(null)}
        />
      )}

      {/* History Sidebar */}
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        t={t}
        chatHistory={chatHistory}
        role={role}
        onNewChat={handleClearChat}
        language={language}
        setLanguage={setLanguage}
        languageOptions={languageOptions}
        onChangeRole={() => {}}
      />
    </div>
  );
}

export default App;



