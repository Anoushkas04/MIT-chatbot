import React from "react";

export default function NotificationToast({ notification, onOpenDrawer, onDismissPopup, drawerOpen, copilotOpen }) {
  if (!notification || drawerOpen) return null;

  const handleDismiss = () => {
    if (onDismissPopup && notification.state_id) {
      onDismissPopup(notification.state_id);
    }
  };

  return (
    <div className={`notification-toast-card fade-in-up ${copilotOpen ? "notification-toast-card--shifted" : ""}`}>
      <div className="toast-badge-row">
        <span className="toast-priority-pill">{notification.priority || "TIME-SENSITIVE EVENT"}</span>
        <button className="toast-close-btn" onClick={handleDismiss}>✕</button>
      </div>

      <div className="toast-main">
        <span className="toast-icon">{notification.icon || "🔔"}</span>
        <div className="toast-content">
          <h4 className="toast-title">{notification.title}</h4>
          {notification.formatted_date && (
            <div style={{ fontSize: "12px", color: "#1E40AF", fontWeight: 700, margin: "2px 0 4px 0" }}>
              📅 Event Date: {notification.formatted_date}
            </div>
          )}
          <p className="toast-desc">{notification.content}</p>
          {notification.source_doc && (
            <span className="toast-source">Source: {notification.source_doc}</span>
          )}
        </div>
      </div>

      <div className="toast-actions">
        <button
          className="toast-action-primary"
          onClick={() => {
            if (onOpenDrawer) onOpenDrawer();
            handleDismiss();
          }}
        >
          View Notification Center →
        </button>
        <button className="toast-action-secondary" onClick={handleDismiss}>
          Dismiss
        </button>
      </div>
    </div>
  );
}
