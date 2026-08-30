const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/* ------------------------------------------------------------------
   1. AUTHENTICATION & PROFILE APIS
   ------------------------------------------------------------------ */

export async function verifyLearnerID(learnerId) {
  const res = await fetch(`${BASE_URL}/api/auth/verify-learner-id`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ learner_id: learnerId }),
  });
  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail || "Learner ID validation failed.");
  }
  return res.json();
}

export async function verifyOTPCode(learnerId, otpCode) {
  const res = await fetch(`${BASE_URL}/api/auth/verify-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ learner_id: learnerId, otp_code: otpCode }),
  });
  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail || "OTP verification failed.");
  }
  return res.json();
}

export async function completeRegistration(payload) {
  const res = await fetch(`${BASE_URL}/api/auth/register-complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail || "Account creation failed.");
  }
  return res.json();
}

export async function loginUser(emailOrId, password) {
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email_or_id: emailOrId, password }),
  });
  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail || "Login failed.");
  }
  return res.json();
}

export async function fetchCurrentUserProfile(token) {
  if (!token) return null;
  const res = await fetch(`${BASE_URL}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return null;
  return res.json();
}

export async function updateUserProfile(token, profileData) {
  const res = await fetch(`${BASE_URL}/api/auth/profile`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(profileData),
  });
  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail || "Failed to update user profile.");
  }
  return res.json();
}

/* ------------------------------------------------------------------
   2. AI COPILOT & RAG APIS
   ------------------------------------------------------------------ */

export async function generateAIResponse(message, role, language, sessionId, context = {}) {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      role,
      language,
      session_id: sessionId,
      department: context.department || null,
      academic_year: context.academicYear || null,
      semester: context.semester || null,
    }),
  });

  if (!res.ok) {
    throw new Error(`Chat request failed with status: ${res.status}`);
  }

  return res.json();
}

/* ------------------------------------------------------------------
   3. ACADEMIC CALENDAR & CUTOFFS APIS
   ------------------------------------------------------------------ */

export async function fetchAcademicCalendar() {
  const res = await fetch(`${BASE_URL}/api/academic/calendar`);
  if (!res.ok) return null;
  return await res.json();
}

export async function fetchCanonicalTimeline(role = "student", dept = "", year = "") {
  const params = new URLSearchParams();
  if (role) params.append("role", role);
  if (dept) params.append("department", dept);
  if (year) params.append("academic_year", year);
  const res = await fetch(`${BASE_URL}/api/academic/timeline?${params.toString()}`);
  if (!res.ok) return { count: 0, events: [] };
  return await res.json();
}

export async function fetchCutoffRanks(course = "B.Tech", roundNum = 1, maxRank = null) {
  const params = new URLSearchParams({ course, round_num: roundNum });
  if (maxRank) params.append("max_rank", maxRank);
  const res = await fetch(`${BASE_URL}/api/academic/cutoffs?${params.toString()}`);
  if (!res.ok) return null;
  return await res.json();
}

/* ------------------------------------------------------------------
   4. FACULTY DIRECTORY APIS
   ------------------------------------------------------------------ */

export async function fetchFacultyDirectory(query = "", dept = "") {
  const params = new URLSearchParams();
  if (query) params.append("query", query);
  if (dept) params.append("dept", dept);
  const res = await fetch(`${BASE_URL}/api/faculty?${params.toString()}`);
  if (!res.ok) return null;
  return await res.json();
}

/* ------------------------------------------------------------------
   5. STUDENT COMMUNITY & VOTING APIS
   ------------------------------------------------------------------ */

export async function fetchCommunityPosts(category = "All") {
  const params = new URLSearchParams();
  if (category && category.toLowerCase() !== "all") {
    params.append("category", category);
  }
  const url = `${BASE_URL}/api/posts${params.toString() ? "?" + params.toString() : ""}`;
  const res = await fetch(url);
  if (!res.ok) return [];
  return await res.json();
}

export async function createCommunityPost(authorOrData, tag, title, content, subCommunity) {
  let payload;
  if (typeof authorOrData === "object" && authorOrData !== null) {
    payload = {
      author_name: authorOrData.author_name || authorOrData.author || "Student",
      tag: authorOrData.tag || "General",
      title: authorOrData.title || "",
      content: authorOrData.content || "",
      sub_community: authorOrData.sub_community || "Hostels",
    };
  } else {
    payload = {
      author_name: authorOrData || "Student",
      tag: tag || "General",
      title: title || "",
      content: content || "",
      sub_community: subCommunity || "Hostels",
    };
  }

  const res = await fetch(`${BASE_URL}/api/posts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json();
    throw new Error(errorData.detail || "Failed to create community post.");
  }
  return await res.json();
}

export async function upvoteCommunityPost(postId) {
  const res = await fetch(`${BASE_URL}/api/posts/${postId}/upvote`, { method: "POST" });
  if (!res.ok) return null;
  return await res.json();
}

export async function downvoteCommunityPost(postId) {
  const res = await fetch(`${BASE_URL}/api/posts/${postId}/downvote`, { method: "POST" });
  if (!res.ok) return null;
  return await res.json();
}

export async function addPostComment(postId, authorName, content) {
  const res = await fetch(`${BASE_URL}/api/posts/${postId}/comments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ author_name: authorName, content }),
  });
  if (!res.ok) return null;
  return await res.json();
}

export async function markCommentHelpful(commentId) {
  const res = await fetch(`${BASE_URL}/api/posts/comments/${commentId}/mark-helpful`, { method: "POST" });
  if (!res.ok) return null;
  return await res.json();
}

export async function fetchContributorLeaderboard() {
  const res = await fetch(`${BASE_URL}/api/posts/leaderboard`);
  if (!res.ok) return [];
  return await res.json();
}

/* ------------------------------------------------------------------
   6. NOTIFICATIONS & TIMELINE APIS
   ------------------------------------------------------------------ */

export async function fetchNotifications(userId = "guest", role = "student", dept = "", year = "") {
  const params = new URLSearchParams({ user_id: userId, role });
  if (dept) params.append("dept", dept);
  if (year) params.append("year", year);
  const res = await fetch(`${BASE_URL}/api/notifications?${params.toString()}`);
  if (!res.ok) return { unread_count: 0, notifications: [], popup_notification: null };
  return await res.json();
}

export async function markNotificationRead(stateId) {
  const res = await fetch(`${BASE_URL}/api/notifications/${stateId}/read`, { method: "POST" });
  if (!res.ok) return null;
  return await res.json();
}

export async function dismissNotification(stateId) {
  const res = await fetch(`${BASE_URL}/api/notifications/${stateId}/dismiss`, { method: "POST" });
  if (!res.ok) return null;
  return await res.json();
}

export async function dismissPopupNotification(stateId) {
  const res = await fetch(`${BASE_URL}/api/notifications/${stateId}/dismiss-popup`, { method: "POST" });
  if (!res.ok) return null;
  return await res.json();
}

export async function dismissAllPopups(userId = "guest") {
  const res = await fetch(`${BASE_URL}/api/notifications/dismiss-all-popups?user_id=${encodeURIComponent(userId)}`, { method: "POST" });
  if (!res.ok) return null;
  return await res.json();
}

export async function markAllNotificationsRead(userId = "guest") {
  const res = await fetch(`${BASE_URL}/api/notifications/read-all?user_id=${encodeURIComponent(userId)}`, { method: "POST" });
  if (!res.ok) return null;
  return await res.json();
}

/* ------------------------------------------------------------------
   7. SYSTEM FEEDBACK APIS
   ------------------------------------------------------------------ */

export async function submitSystemFeedback(feedbackType, message, rating = 5) {
  const res = await fetch(`${BASE_URL}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feedback_type: feedbackType, message, rating }),
  });
  if (!res.ok) return null;
  return await res.json();
}

/* ------------------------------------------------------------------
   8. ADMIN OPERATIONS APIS
   ------------------------------------------------------------------ */

export async function fetchAdminAnalytics() {
  const res = await fetch(`${BASE_URL}/api/admin/analytics`);
  if (!res.ok) return null;
  return await res.json();
}

export async function fetchAdminUsers() {
  const res = await fetch(`${BASE_URL}/api/admin/users`);
  if (!res.ok) return null;
  return await res.json();
}

export async function reindexDocuments() {
  const res = await fetch(`${BASE_URL}/api/admin/reindex`, { method: "POST" });
  if (!res.ok) return null;
  return await res.json();
}

export async function fetchAdminEvents(token = null) {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await fetch(`${BASE_URL}/api/admin/events`, { headers });
  if (!res.ok) return { count: 0, events: [] };
  return await res.json();
}

export async function createAdminEvent(token, payload) {
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const res = await fetch(`${BASE_URL}/api/admin/events`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create timeline event.");
  }
  return await res.json();
}

export async function updateAdminEvent(token, eventId, payload) {
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const res = await fetch(`${BASE_URL}/api/admin/events/${eventId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update timeline event.");
  }
  return await res.json();
}

export async function deleteAdminEvent(token, eventId) {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await fetch(`${BASE_URL}/api/admin/events/${eventId}`, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) return null;
  return await res.json();
}

export async function toggleAdminEventStatus(token, eventId) {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await fetch(`${BASE_URL}/api/admin/events/${eventId}/toggle-status`, {
    method: "POST",
    headers,
  });
  if (!res.ok) return null;
  return await res.json();
}

/* ------------------------------------------------------------------
   9. STUDENT REWARDS & REPUTATION APIS
   ------------------------------------------------------------------ */

export async function fetchUserRewards(token = null) {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await fetch(`${BASE_URL}/api/rewards/me`, { headers });
  if (!res.ok) return null;
  return await res.json();
}

export async function fetchMultiPeriodLeaderboard(timeframe = "weekly") {
  const res = await fetch(`${BASE_URL}/api/rewards/leaderboard?timeframe=${timeframe}`);
  if (!res.ok) return null;
  return await res.json();
}

/* ------------------------------------------------------------------
   10. GLOBAL SEARCH APIS
   ------------------------------------------------------------------ */

export async function fetchAdminViolations(token = null) {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await fetch(`${BASE_URL}/api/admin/moderation`, { headers });
  if (!res.ok) return { count: 0, violations: [] };
  return await res.json();
}

export async function performGlobalSearch(query = "", category = "all") {
  const params = new URLSearchParams();
  if (query) params.append("q", query);
  if (category) params.append("category", category);
  const res = await fetch(`${BASE_URL}/api/search?${params.toString()}`);
  if (!res.ok) return null;
  return await res.json();
}

export async function fetchDepartments() {
  const res = await fetch(`${BASE_URL}/api/departments`);
  if (!res.ok) return null;
  return await res.json();
}
