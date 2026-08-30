import React, { useState } from "react";

export default function NotificationsDrawer({
  isOpen,
  onClose,
  notifications = [],
  unreadCount = 0,
  onMarkAllRead,
  onMarkSingleRead,
  onDismissNotification,
}) {
  const [filterCategory, setFilterCategory] = useState("All");

  if (!isOpen) return null;

  const categories = [
    { id: "All", label: "🌐 All" },
    { id: "Exams", label: "📝 Exams" },
    { id: "Deadlines", label: "⏳ Deadlines" },
    { id: "Academic", label: "🎓 Academic" },
    { id: "Placements", label: "💼 Placements" },
    { id: "Financial", label: "💳 Financial" },
    { id: "Events", label: "🎪 Events" },
  ];

  const filteredNotifs =
    filterCategory === "All"
      ? notifications
      : notifications.filter((n) => n.category?.toLowerCase() === filterCategory.toLowerCase());

  return (
    <div className="inspector-overlay" onClick={onClose}>
      <div className="inspector-drawer notifications-drawer" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="inspector-header">
          <div className="inspector-title-group">
            <span className="inspector-icon">🔔</span>
            <div>
              <h3 className="inspector-title">Timeline Notification Center</h3>
              <p className="inspector-subtitle">Live time-threshold alerts grounded in MIT academic calendar</p>
            </div>
          </div>
          <button className="inspector-close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Category Filter Tabs */}
        <div className="notif-category-tabs">
          {categories.map((cat) => (
            <button
              key={cat.id}
              className={`cat-tab-btn ${filterCategory === cat.id ? "active" : ""}`}
              onClick={() => setFilterCategory(cat.id)}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Action bar */}
        <div className="notif-action-bar">
          <span className="notif-count">
            {unreadCount > 0 ? `🔴 ${unreadCount} Unread Notifications` : "✓ All notifications read"}
          </span>
          {unreadCount > 0 && (
            <button className="text-link" onClick={onMarkAllRead}>
              Mark All as Read
            </button>
          )}
        </div>

        {/* Notifications list */}
        <div className="notifications-list">
          {filteredNotifs.length > 0 ? (
            filteredNotifs.map((n) => (
              <div key={n.state_id || n.event_id} className={`notification-card ${!n.read ? "unread" : ""}`}>
                <div className="notif-header">
                  <span className="notif-icon">{n.icon || "🔔"}</span>
                  <div className="notif-title-group">
                    <div className="notif-title-row">
                      <h4 className="notif-title">{n.title}</h4>
                      <span className={`severity-badge ${n.type_color || "blue"}`}>
                        {n.priority}
                      </span>
                    </div>
                    
                    {/* Actual Calendar Date & Relative Countdown */}
                    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "10px", marginTop: "4px", fontSize: "12px" }}>
                      {n.formatted_date && (
                        <span style={{ color: "#1E40AF", fontWeight: 800, background: "#EFF6FF", padding: "2px 8px", borderRadius: "6px", border: "1px solid #BFDBFE" }}>
                          📅 Event Date: {n.formatted_date}
                        </span>
                      )}
                      <span className="notif-time" style={{ color: "#64748B", fontWeight: 600 }}>⏱️ {n.time}</span>
                    </div>
                  </div>
                </div>

                <p className="notif-body" style={{ marginTop: "8px" }}>{n.content}</p>

                {n.source_doc && (
                  <div className="notif-source-pill" style={{ marginTop: "6px" }}>
                    📄 Grounded Source: {n.source_doc}
                  </div>
                )}

                <div className="notif-card-actions" style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
                  {!n.read && (
                    <button
                      className="read-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onMarkSingleRead) onMarkSingleRead(n.state_id);
                      }}
                      style={{ padding: "6px 14px", background: "#2563EB", color: "#fff", border: "none", borderRadius: "6px", fontSize: "12px", fontWeight: 700, cursor: "pointer" }}
                    >
                      ✓ Mark Read
                    </button>
                  )}

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onDismissNotification) onDismissNotification(n.state_id);
                    }}
                    style={{ padding: "6px 14px", background: "#F1F5F9", color: "#475569", border: "1px solid #CBD5E1", borderRadius: "6px", fontSize: "12px", fontWeight: 700, cursor: "pointer" }}
                  >
                    🗑️ Dismiss
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="no-notifs" style={{ padding: "30px", textAlign: "center", color: "#64748B", fontSize: "13px" }}>
              No notifications active in this category.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="inspector-footer">
          <span className="footer-note">MIT CampusOS Timeline Notification Engine • Grounded in Canonical Database Events</span>
        </div>
      </div>
    </div>
  );
}
