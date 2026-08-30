import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

const ROLE_META = {
  student:     { icon: "🎓", label: "Student",    pill: "Current Student" },
  prospective: { icon: "🌟", label: "Applicant",  pill: "Prospective Student" },
  parent:      { icon: "🏛️", label: "Campus Info", pill: "Campus Info & Admissions" },
  faculty:     { icon: "👨‍🏫", label: "Faculty",    pill: "Faculty Member" },
};

export default function ChatWindow({
  t,
  messages,
  isTyping,
  input,
  setInput,
  onSend,
  role,
  language,
  setLanguage,
  languageOptions,
  onMenuOpen,
  onClearChat,
  onChangeRole,
  isDrawer = false,
  onCloseDrawer,
  onInspectCitation,
  onOpenFeedback,
  department = "Computer Science & Engg",
  academicYear = "3rd Year",
  semester = "Even Semester",
}) {
  const bottomRef   = useRef(null);
  const chatBodyRef = useRef(null);
  const textareaRef = useRef(null);
  const [langOpen, setLangOpen] = useState(false);
  const langRef = useRef(null);

  const meta        = ROLE_META[role] || ROLE_META.student;
  const suggestions = t.suggestions?.[role] || [];

  // Get dynamic follow-ups from the last AI message
  const lastAiMsg = [...messages].reverse().find((m) => m.role === "assistant");
  const dynamicFollowups = lastAiMsg?.followups || [];

  useEffect(() => {
    // Only auto-scroll if the user is already near the bottom — don't yank
    // them back down if they've scrolled up to reread earlier messages.
    const body = chatBodyRef.current;
    const nearBottom = !body || body.scrollHeight - body.scrollTop - body.clientHeight < 120;
    if (nearBottom) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  useEffect(() => {
    const handler = (e) => {
      if (langRef.current && !langRef.current.contains(e.target)) {
        setLangOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleInput = (e) => {
    setInput(e.target.value);
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 140) + "px";
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className={`chat-root ${isDrawer ? "chat-drawer-mode" : ""}`} role="main">
      {/* ── Header ── */}
      <header className="chat-header" role="banner">
        <div className="chat-header-left">
          {onMenuOpen && (
            <button
              className="icon-btn"
              onClick={onMenuOpen}
              aria-label="Open navigation menu"
            >
              <div className="hamburger-icon" aria-hidden="true">
                <span /><span /><span />
              </div>
            </button>
          )}

          <div className="header-wordmark">
            <div className="header-logo-badge" aria-hidden="true">AI</div>
            <div className="header-info">
              <span className="header-title">Campus Assistant</span>
              <div className="header-role-pill">
                {meta.icon} {meta.pill}
              </div>
            </div>
          </div>
        </div>

        <div className="chat-header-right">
          {/* Clear chat */}
          <button
            className="icon-btn"
            onClick={onClearChat}
            aria-label={t.clearChat}
            title={t.clearChat}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6l-1 14H6L5 6" />
              <path d="M10 11v6M14 11v6" />
              <path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2" />
            </svg>
          </button>

          {isDrawer && onCloseDrawer && (
            <button
              className="icon-btn drawer-close-icon"
              onClick={onCloseDrawer}
              title="Close AI Copilot Drawer"
            >
              ✕
            </button>
          )}
        </div>
      </header>

      {/* ── Chat Body ── */}
      <div className="chat-body" ref={chatBodyRef} role="log" aria-label="Chat messages" aria-live="polite">
        {messages.length === 0 ? (
          /* Welcome screen */
          <div className="welcome-wrap">
            <h2 className="welcome-heading">Campus Information Assistant</h2>
            <p className="welcome-sub">
              Ask about admissions, placements, faculty, academic calendar, or campus facilities.
              Answers grounded in official MIT Manipal documents.
            </p>

            {/* Personalized quick suggestions */}
            <div className="suggestions-grid" role="group" aria-label="Suggested questions">
              {(department?.includes("Mechanical") ? [
                "Tell me about the Industrial Robotics Lab AB1 viva guidelines for Mechanical students",
                "What are Bosch and Tata Motors placement CGPA cutoffs for Mechanical?",
                "Where can I access SolidWorks and ANSYS software licenses in AB1?"
              ] : [
                "What are the top DSA topics for Microsoft and Amazon placement drives?",
                "What GPU facilities are available in AB5 3rd Floor Compute Lab?",
                "Which 6th/8th semester electives are recommended for Computer Science?"
              ]).concat(suggestions || []).slice(0, 5).map((s, i) => (
                <button
                  key={i}
                  className="suggestion-btn"
                  onClick={() => onSend(s)}
                  aria-label={`Ask: ${s}`}
                >
                  {s}
                  <span className="suggestion-arrow" aria-hidden="true">→</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Messages */
          <div className="messages-area">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                msg={msg}
                t={t}
                roleMeta={meta}
                onInspectCitation={onInspectCitation}
                onOpenFeedback={onOpenFeedback}
                language={language}
              />
            ))}
            {isTyping && <TypingIndicator t={t} />}

            {/* Dynamic Follow-up Suggestions Chips */}
            {!isTyping && dynamicFollowups.length > 0 && (
              <div className="followup-suggestions-block">
                <span className="followup-label">Suggested follow-ups:</span>
                <div className="followup-chips-row">
                  {dynamicFollowups.map((q, idx) => (
                    <button
                      key={idx}
                      className="followup-chip"
                      onClick={() => onSend(q)}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div ref={bottomRef} aria-hidden="true" />
          </div>
        )}
      </div>

      {/* ── Input Bar ── */}
      <div className="input-outer" role="form" aria-label="Message input">
        <div className="input-container">
          <div className="input-box">
            <textarea
              ref={textareaRef}
              id="chat-input"
              className="chat-input"
              placeholder={t.placeholder}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKey}
              rows={1}
              aria-label="Type your message"
              aria-multiline="true"
            />
            <button
              className="send-btn"
              onClick={() => onSend()}
              disabled={!input.trim() || isTyping}
              id="send-btn"
              aria-label={t.send}
            >
              <svg viewBox="0 0 24 24" fill="currentColor" width="17" height="17">
                <path d="M2 12L22 2 12 22 10 14 2 12z" />
              </svg>
            </button>
          </div>
          <div className="input-hint" aria-hidden="true">
            <kbd>Enter</kbd> to send &nbsp;·&nbsp; <kbd>Shift + Enter</kbd> for new line
          </div>
        </div>
      </div>
    </div>
  );
}

