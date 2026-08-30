import React, { useState, useEffect } from "react";
import {
  fetchCommunityPosts,
  createCommunityPost,
  upvoteCommunityPost,
  downvoteCommunityPost,
  addPostComment,
  markCommentHelpful,
  fetchFacultyDirectory,
  fetchContributorLeaderboard,
  updateUserProfile,
  fetchCanonicalTimeline,
} from "../api";
import { OFFICIAL_MIT_DEPARTMENTS } from "../departments";

export default function StudentCorner({
  user,
  token,
  onUpdateProfile,
  onPromptSelect,
  department,
  setDepartment,
  academicYear,
  setAcademicYear,
  semester,
  setSemester,
  t,
  onOpenRewardsModal,
}) {
  const [activeTab, setActiveTab] = useState("community"); // "community" | "overview" | "faculty"
  const [subCategory, setSubCategory] = useState("All");

  // Timeline State
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [isLoadingTimeline, setIsLoadingTimeline] = useState(false);
  const [, setTicker] = useState(0);

  useEffect(() => {
    if (activeTab === "overview") {
      loadTimeline();
    }
  }, [activeTab, department, academicYear]);

  useEffect(() => {
    const interval = setInterval(() => {
      setTicker((t) => t + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const loadTimeline = async () => {
    setIsLoadingTimeline(true);
    try {
      const res = await fetchCanonicalTimeline(user?.role || "student", department, academicYear);
      if (res && res.events) {
        setTimelineEvents(res.events);
      }
    } catch (err) {
      console.warn("Timeline fetch error:", err);
    } finally {
      setIsLoadingTimeline(false);
    }
  };

  // Profile Edit Modal State
  const [showEditProfileModal, setShowEditProfileModal] = useState(false);
  const [editDept, setEditDept] = useState(department || "Computer Science & Engineering");
  const [editYear, setEditYear] = useState(academicYear || "3rd Year (2023-27)");
  const [editSem, setEditSem] = useState(semester || "Even Semester (Jan - May)");
  const [editBio, setEditBio] = useState(user?.bio || "");
  const [editSkills, setEditSkills] = useState(user?.skills || "");
  const [editInterests, setEditInterests] = useState(user?.interests || "");
  const [editActivities, setEditActivities] = useState(user?.activities || "");
  const [editAvatar, setEditAvatar] = useState(user?.avatar_icon || "🎓");
  const [profileSaveLoading, setProfileSaveLoading] = useState(false);
  const [profileSaveMsg, setProfileSaveMsg] = useState("");

  // Leaderboard State
  const [leaderboard, setLeaderboard] = useState([]);

  // Faculty Directory State
  const [facultySearch, setFacultySearch] = useState("");
  const [facultyDept, setFacultyDept] = useState("All");
  const [facultyList, setFacultyList] = useState([]);
  const [isLoadingFaculty, setIsLoadingFaculty] = useState(false);

  // Posts State
  const [communityPosts, setCommunityPosts] = useState([]);
  const [newPost, setNewPost] = useState({ title: "", content: "", sub_community: "Hostels", tag: "General" });
  const [postSubmitted, setPostSubmitted] = useState(false);
  const [categoryError, setCategoryError] = useState("");
  const [isLoadingPosts, setIsLoadingPosts] = useState(false);

  const handleQuickPromptSelect = (title, content, category) => {
    setNewPost({
      title: title || "",
      content: content || "",
      sub_community: category || "General",
      tag: "General",
    });
    setCategoryError("");
    const el = document.getElementById("create-post-title");
    if (el) {
      el.focus();
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  // Active post for commenting
  const [activeCommentPostId, setActiveCommentPostId] = useState(null);
  const [commentInput, setCommentInput] = useState("");

  useEffect(() => {
    loadLeaderboard();
  }, []);

  const loadLeaderboard = async () => {
    const data = await fetchContributorLeaderboard();
    if (data && Array.isArray(data)) {
      setLeaderboard(data);
    }
  };

  useEffect(() => {
    if (activeTab === "faculty") {
      loadFaculty(facultySearch, facultyDept);
    }
  }, [activeTab, facultySearch, facultyDept]);

  const loadFaculty = async (search = facultySearch, dept = facultyDept) => {
    setIsLoadingFaculty(true);
    try {
      const res = await fetchFacultyDirectory(search, dept);
      if (res && res.data) {
        setFacultyList(res.data);
      } else {
        setFacultyList([]);
      }
    } catch (err) {
      console.warn("Faculty directory fetch error:", err);
      setFacultyList([]);
    } finally {
      setIsLoadingFaculty(false);
    }
  };

  useEffect(() => {
    loadPosts(subCategory);
  }, [subCategory]);

  const loadPosts = async (cat = subCategory) => {
    setIsLoadingPosts(true);
    try {
      const data = await fetchCommunityPosts(cat);
      if (data && Array.isArray(data)) {
        setCommunityPosts(data);
      } else {
        setCommunityPosts([]);
      }
    } catch (err) {
      console.warn("Failed to load community posts:", err);
      setCommunityPosts([]);
    } finally {
      setIsLoadingPosts(false);
    }
  };

  const handlePostSubmit = async (e) => {
    e.preventDefault();
    setCategoryError(null);
    if (!newPost.title.trim() || !newPost.content.trim()) return;

    try {
      const created = await createCommunityPost(
        user?.name || "Verified Student",
        newPost.tag,
        newPost.title,
        newPost.content,
        newPost.sub_community
      );

      setCommunityPosts([created, ...communityPosts]);
      setNewPost({ title: "", content: "", sub_community: "Hostels", tag: "General" });
      setPostSubmitted(true);
      setTimeout(() => setPostSubmitted(false), 4000);
    } catch (err) {
      setCategoryError(err.message || "Failed to create post.");
    }
  };

  const handleUpvote = async (postId) => {
    setCommunityPosts(
      communityPosts.map((p) => (p.id === postId ? { ...p, upvotes: p.upvotes + 1 } : p))
    );
    await upvoteCommunityPost(postId);
  };

  const handleDownvote = async (postId) => {
    setCommunityPosts(
      communityPosts.map((p) => (p.id === postId ? { ...p, downvotes: (p.downvotes || 0) + 1 } : p))
    );
    await downvoteCommunityPost(postId);
  };

  const handleAddComment = async (postId) => {
    if (!commentInput.trim()) return;
    const added = await addPostComment(postId, user?.name || "Student", commentInput);
    if (added) {
      setCommunityPosts(
        communityPosts.map((p) => {
          if (p.id === postId) {
            return { ...p, comments: [...(p.comments || []), added] };
          }
          return p;
        })
      );
      setCommentInput("");
    }
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setProfileSaveLoading(true);
    setProfileSaveMsg("");
    try {
      const payload = {
        department: editDept,
        academic_year: editYear,
        semester: editSem,
        avatar_icon: editAvatar,
        bio: editBio,
        skills: editSkills,
        interests: editInterests,
        activities: editActivities,
      };

      const updated = await updateUserProfile(token, payload);
      setDepartment(editDept);
      setAcademicYear(editYear);
      setSemester(editSem);
      if (onUpdateProfile) onUpdateProfile(updated);
      setProfileSaveMsg("✓ Profile and academic information updated and saved to server!");
      setTimeout(() => {
        setShowEditProfileModal(false);
        setProfileSaveMsg("");
      }, 1200);
    } catch (err) {
      setProfileSaveMsg(`⚠️ Update failed: ${err.message}`);
    } finally {
      setProfileSaveLoading(false);
    }
  };

  const categoriesTaxonomy = [
    { id: "All", label: "🔥 All", icon: "🌐" },
    { id: "Academics", label: "📚 Academics", icon: "📖" },
    { id: "Campus Life", label: "🎉 Campus Life", icon: "✨" },
    { id: "Hostels", label: "🏠 Hostels", icon: "🏢" },
    { id: "Mess", label: "🍱 Mess & Food", icon: "🍕" },
    { id: "Clubs", label: "🏆 Clubs & Tech", icon: "⚙️" },
    { id: "Events", label: "🎪 Events & Revels", icon: "🎭" },
    { id: "Transportation", label: "🚌 Transportation", icon: "🛵" },
    { id: "Resources", label: "🖨️ Resources & Xerox", icon: "📄" },
    { id: "General", label: "💬 General", icon: "🗣️" },
    { id: "Lost & Found", label: "🔍 Lost & Found", icon: "🔎" },
    { id: "Advice", label: "💡 Senior Advice", icon: "⭐" },
  ];

  const filteredPosts =
    subCategory === "All"
      ? communityPosts
      : communityPosts.filter((p) => p.sub_community?.toLowerCase().includes(subCategory.toLowerCase()));

  return (
    <div className="workspace-container">
      {/* Header */}
      <div className="workspace-header">
        <div className="header-left">
          <div className="header-badge">🎓 Authenticated Student Workspace</div>
          <h1 className="header-title">Welcome back, {user?.name || "Student"}! 👋</h1>
          <p className="header-desc">
            {department || "Computer Science & Engineering"} • {academicYear || "3rd Year"} • {semester || "Even Semester"}
          </p>

          <div style={{ marginTop: "8px", display: "flex", gap: "8px", flexWrap: "wrap", fontSize: "11px", fontWeight: 700, color: "#1E293B" }}>
            {user?.learner_id && (
              <span className="pill-tag blue">🆔 Learner ID: {user.learner_id} (Read-only)</span>
            )}
            {user?.registration_number && (
              <span className="pill-tag purple">🔢 Reg No: {user.registration_number} (Read-only)</span>
            )}
            {user?.admission_year && (
              <span className="pill-tag teal">📅 Admission Year: {user.admission_year} (Read-only)</span>
            )}
            <button
              onClick={onOpenRewardsModal}
              style={{ padding: "4px 12px", background: "#FEF3C7", color: "#B45309", border: "1px solid #FDE68A", borderRadius: "12px", fontSize: "11px", fontWeight: 800, cursor: "pointer", display: "inline-flex", alignItems: "center", gap: "4px" }}
            >
              🏆 {user?.rewards_points || 0} Campus Points • Tap for Scorecard 🎖️
            </button>
            <button
              onClick={() => setShowEditProfileModal(true)}
              style={{ padding: "4px 10px", background: "#2563EB", color: "#FFFFFF", border: "none", borderRadius: "12px", fontSize: "11px", fontWeight: 700, cursor: "pointer" }}
            >
              ✏️ Edit Profile & Academic Info
            </button>
          </div>
        </div>

        {/* Personalization Card */}
        <div className="personalization-card">
          <div className="p-card-title">⚙️ Quick Academic Settings</div>
          <div className="p-card-grid">
            <div className="p-field">
              <label>Branch / Department:</label>
              <select value={department} onChange={(e) => setDepartment(e.target.value)}>
                {OFFICIAL_MIT_DEPARTMENTS.map((d) => (
                  <option key={d.code} value={d.name}>
                    {d.code} — {d.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="p-field">
              <label>Academic Year:</label>
              <select value={academicYear} onChange={(e) => setAcademicYear(e.target.value)}>
                <option value="1st Year (2025-29)">1st Year (Freshman)</option>
                <option value="2nd Year (2024-28)">2nd Year (Sophomore)</option>
                <option value="3rd Year (2023-27)">3rd Year (Junior)</option>
                <option value="4th Year (2022-26)">4th Year (Senior)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Sub Navigation */}
      <div className="workspace-tabs">
        <button
          className={`w-tab ${activeTab === "community" ? "active" : ""}`}
          onClick={() => setActiveTab("community")}
        >
          💬 Student Community Feed ({filteredPosts.length})
        </button>
        <button
          className={`w-tab ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          📊 Academic Overview & Countdown
        </button>
        <button
          className={`w-tab ${activeTab === "faculty" ? "active" : ""}`}
          onClick={() => setActiveTab("faculty")}
        >
          👨‍🏫 Faculty & Cabin Directory
        </button>
      </div>

      {/* 1. COMMUNITY TAB */}
      {activeTab === "community" && (
        <div className="community-layout fade-in">
          {/* Larger & More Prominent Category Filter Bar */}
          <div className="category-scroll-bar" style={{ display: "flex", gap: "10px", overflowX: "auto", padding: "10px 4px 14px 4px", marginBottom: "16px" }}>
            {categoriesTaxonomy.map((cat) => {
              const isActive = subCategory === cat.id;
              return (
                <button
                  key={cat.id}
                  onClick={() => setSubCategory(cat.id)}
                  style={{
                    padding: "10px 18px",
                    background: isActive ? "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)" : "#FFFFFF",
                    color: isActive ? "#FFFFFF" : "#334155",
                    border: isActive ? "1px solid #1D4ED8" : "1px solid #CBD5E1",
                    borderRadius: "12px",
                    fontSize: "13.5px",
                    fontWeight: 700,
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px",
                    whiteSpace: "nowrap",
                    boxShadow: isActive ? "0 4px 14px rgba(37, 99, 235, 0.3)" : "0 2px 4px rgba(15, 23, 42, 0.03)",
                    transition: "all 0.2s ease",
                    transform: isActive ? "scale(1.03)" : "none"
                  }}
                >
                  <span style={{ fontSize: "17px" }}>{cat.icon}</span> {cat.id}
                </button>
              );
            })}
          </div>

          <div className="community-grid">
            {/* Feed Column */}
            <div className="feed-column">
              {isLoadingPosts ? (
                <div style={{ textAlign: "center", padding: "40px", color: "#64748B" }}>
                  <span>⏳ Loading community discussions...</span>
                </div>
              ) : filteredPosts.length > 0 ? (
                filteredPosts.map((post) => (
                  <div key={post.id} className="post-card">
                    <div className="post-card-header">
                      <span className="author-avatar">🎓</span>
                      <div className="author-info">
                        <div className="author-name-row">
                          <span className="author-name">{post.author}</span>
                          {post.verified && <span className="verified-badge">✓ Verified</span>}
                        </div>
                        <span className="post-meta">
                          {post.sub_community} • {post.time}
                        </span>
                      </div>
                    </div>

                    <h3 className="post-title">{post.title}</h3>
                    <p className="post-content">{post.content}</p>

                    <div className="post-actions-bar">
                      <div className="vote-group">
                        <button className="vote-btn up" onClick={() => handleUpvote(post.id)}>
                          ▲ {post.upvotes}
                        </button>
                        <button className="vote-btn down" onClick={() => handleDownvote(post.id)}>
                          ▼ {post.downvotes || 0}
                        </button>
                      </div>

                      <button
                        className="comment-toggle-btn"
                        onClick={() => setActiveCommentPostId(activeCommentPostId === post.id ? null : post.id)}
                      >
                        💬 {post.comments ? post.comments.length : 0} Answers
                      </button>
                    </div>

                    {/* Comments drawer */}
                    {activeCommentPostId === post.id && (
                      <div className="comments-section fade-in">
                        <div className="comments-list">
                          {post.comments && post.comments.length > 0 ? (
                            post.comments.map((c) => (
                              <div key={c.id} className={`comment-card ${c.is_helpful ? "helpful" : ""}`}>
                                <div className="comment-header">
                                  <span className="comment-author">{c.author}</span>
                                  {c.is_helpful && <span className="helpful-tag">★ Accepted Helpful Answer</span>}
                                </div>
                                <p className="comment-text">{c.content}</p>
                              </div>
                            ))
                          ) : (
                            <div className="no-comments" style={{ padding: "12px", fontSize: "12px", color: "#64748B" }}>
                              No answers yet. Be the first to reply!
                            </div>
                          )}
                        </div>

                        <div className="comment-input-row" style={{ display: "flex", gap: "8px", marginTop: "10px" }}>
                          <input
                            type="text"
                            placeholder="Write your answer..."
                            value={commentInput}
                            onChange={(e) => setCommentInput(e.target.value)}
                            style={{ flex: 1, padding: "8px", borderRadius: "6px", border: "1px solid #CBD5E1", fontSize: "13px" }}
                          />
                          <button
                            onClick={() => handleAddComment(post.id)}
                            style={{ padding: "8px 14px", background: "#2563EB", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 700, cursor: "pointer", fontSize: "13px" }}
                          >
                            Reply
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                /* STRICT AUTHORITATIVE & INTERACTIVE EMPTY STATE WHEN 0 POSTS EXIST */
                <div className="empty-community-state" style={{ padding: "36px 28px", textAlign: "center", background: "#FFFFFF", border: "1px solid #CBD5E1", borderRadius: "16px", marginTop: "12px", boxShadow: "0 10px 25px -5px rgba(15, 23, 42, 0.04)" }}>
                  <div style={{ width: "64px", height: "64px", background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px auto", fontSize: "28px", color: "#2563EB" }}>
                    💬
                  </div>

                  <h3 style={{ fontSize: "19px", fontWeight: 800, color: "#0F172A", margin: 0 }}>
                    MIT Manipal Peer Knowledge Exchange
                  </h3>
                  <p style={{ fontSize: "13px", color: "#64748B", marginTop: "6px", maxWidth: "480px", margin: "6px auto 20px auto", lineHeight: 1.5 }}>
                    No community posts in <strong>"{subCategory}"</strong> yet. Be the first student to launch a topic or query for your peers across departments!
                  </p>

                  {/* Sample Discussion Starters Inside Empty State */}
                  <div style={{ background: "#F8FAFC", border: "1px dashed #CBD5E1", borderRadius: "12px", padding: "16px", maxWidth: "520px", margin: "0 auto 20px auto", textAlign: "left" }}>
                    <div style={{ fontSize: "11px", fontWeight: 800, color: "#475569", textTransform: "uppercase", marginBottom: "10px", letterSpacing: "0.5px" }}>
                      💡 Popular Discussion Starters (Click to pre-fill question form):
                    </div>
                    
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      <button
                        type="button"
                        onClick={() => handleQuickPromptSelect("What are the quietest floor study zones in Central Library?", "Looking for quiet spots for mid-sem exam revision in Central Library.", "Academics")}
                        style={{ textAlign: "left", padding: "8px 12px", background: "#FFFFFF", border: "1px solid #E2E8F0", borderRadius: "8px", fontSize: "12px", fontWeight: 600, color: "#1E293B", cursor: "pointer", transition: "all 0.2s" }}
                      >
                        ⚡ "What are the quietest floor study zones in Central Library?"
                      </button>

                      <button
                        type="button"
                        onClick={() => handleQuickPromptSelect("Where can I get color prints for lab manuals after 8 PM in AB5?", "Need urgent lab manual printing details near AB5 or Student Plaza.", "Resources")}
                        style={{ textAlign: "left", padding: "8px 12px", background: "#FFFFFF", border: "1px solid #E2E8F0", borderRadius: "8px", fontSize: "12px", fontWeight: 600, color: "#1E293B", cursor: "pointer", transition: "all 0.2s" }}
                      >
                        ⚡ "Where can I get color prints for lab manuals after 8 PM in AB5?"
                      </button>

                      <button
                        type="button"
                        onClick={() => handleQuickPromptSelect("What is the official procedure for hostel outstation leave pass?", "Step-by-step procedure for parent email verification & warden signoff.", "Hostels")}
                        style={{ textAlign: "left", padding: "8px 12px", background: "#FFFFFF", border: "1px solid #E2E8F0", borderRadius: "8px", fontSize: "12px", fontWeight: 600, color: "#1E293B", cursor: "pointer", transition: "all 0.2s" }}
                      >
                        ⚡ "What is the official procedure for hostel outstation leave pass?"
                      </button>
                    </div>
                  </div>

                  <button
                    className="post-submit-btn"
                    onClick={() => {
                      const el = document.getElementById("create-post-title");
                      if (el) {
                        el.focus();
                        el.scrollIntoView({ behavior: "smooth", block: "center" });
                      }
                    }}
                    style={{ margin: "0 auto", padding: "12px 24px", fontSize: "13px", fontWeight: 800, borderRadius: "10px", background: "#2563EB", boxShadow: "0 4px 12px rgba(37, 99, 235, 0.25)" }}
                  >
                    Start a Campus Discussion ✍️ (+10 Points)
                  </button>
                </div>
              )}
            </div>

            {/* Sidebar Column */}
            <div className="sidebar-column">
              {/* Compact Reputation Scorecard Mini-Corner */}
              <div
                onClick={onOpenRewardsModal}
                style={{
                  background: "linear-gradient(135deg, #EFF6FF 0%, #FFFFFF 100%)",
                  border: "1px solid #BFDBFE",
                  borderRadius: "14px",
                  padding: "14px 16px",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  boxShadow: "0 4px 12px rgba(37, 99, 235, 0.05)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center"
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <div style={{ width: "36px", height: "36px", background: "#DBEAFE", borderRadius: "10px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px" }}>
                    🏆
                  </div>
                  <div>
                    <h4 style={{ margin: 0, fontSize: "13px", fontWeight: 800, color: "#0F172A" }}>My Reputation Scorecard</h4>
                    <span style={{ fontSize: "11px", color: "#2563EB", fontWeight: 700 }}>{user?.rewards_points || 0} Points • Tap for Full Scorecard 🎖️</span>
                  </div>
                </div>
                <span style={{ fontSize: "14px", fontWeight: 800, color: "#2563EB" }}>→</span>
              </div>

              {/* Highly Engaging Ask Campus Community Card */}
              <div
                className="create-post-card"
                style={{
                  background: "#FFFFFF",
                  border: "1px solid #CBD5E1",
                  borderRadius: "16px",
                  padding: "20px",
                  marginTop: "16px",
                  boxShadow: "0 10px 25px -5px rgba(15, 23, 42, 0.05)"
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
                  <div style={{ width: "36px", height: "36px", background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "10px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px" }}>
                    ✍️
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: "15px", fontWeight: 800, color: "#0F172A" }}>Ask Campus Community</h3>
                    <span style={{ fontSize: "11px", color: "#64748B" }}>Get verified answers from peers & seniors</span>
                  </div>
                </div>

                <p style={{ fontSize: "12px", color: "#475569", margin: "10px 0 14px 0", lineHeight: 1.4 }}>
                  Post questions about mess menus, electives, hostel leave approvals, or lab printing.
                </p>

                {categoryError && (
                  <div style={{ padding: "10px 14px", background: "#FEF2F2", border: "1px solid #FECACA", color: "#991B1B", borderRadius: "8px", fontSize: "12px", marginBottom: "12px", fontWeight: 600 }}>
                    ⚠️ {categoryError}
                  </div>
                )}

                {postSubmitted && (
                  <div style={{ padding: "10px 14px", background: "#F0FDF4", border: "1px solid #BBF7D0", color: "#166534", borderRadius: "8px", fontSize: "12px", marginBottom: "12px", fontWeight: 700 }}>
                    ✓ Question posted to campus database! Earned +10 Student Points 🏆
                  </div>
                )}

                <form onSubmit={handlePostSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "11px", fontWeight: 800, color: "#334155", marginBottom: "4px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                      Category / Topic:
                    </label>
                    <select
                      value={newPost.sub_community}
                      onChange={(e) => setNewPost({ ...newPost, sub_community: e.target.value })}
                      style={{ width: "100%", padding: "10px 12px", borderRadius: "8px", border: "1px solid #CBD5E1", fontSize: "13px", fontWeight: 600, color: "#0F172A", background: "#F8FAFC" }}
                    >
                      {categoriesTaxonomy.filter((c) => c.id !== "All").map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.icon} {c.id}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label style={{ display: "block", fontSize: "11px", fontWeight: 800, color: "#334155", marginBottom: "4px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                      Question Title:
                    </label>
                    <input
                      id="create-post-title"
                      type="text"
                      placeholder="e.g. Which library floor is quietest for mid-sem prep?"
                      value={newPost.title}
                      onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
                      required
                      style={{ width: "100%", padding: "10px 12px", borderRadius: "8px", border: "1px solid #CBD5E1", fontSize: "13px", fontWeight: 600, color: "#0F172A" }}
                    />
                  </div>

                  <div>
                    <label style={{ display: "block", fontSize: "11px", fontWeight: 800, color: "#334155", marginBottom: "4px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                      Details / Context:
                    </label>
                    <textarea
                      rows={3}
                      placeholder="Provide extra details for your peers (e.g. course code, block number)..."
                      value={newPost.content}
                      onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
                      required
                      style={{ width: "100%", padding: "10px 12px", borderRadius: "8px", border: "1px solid #CBD5E1", fontSize: "13px", color: "#0F172A", resize: "vertical" }}
                    />
                  </div>

                  <div style={{ background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "8px", padding: "8px 12px", fontSize: "11px", color: "#1E40AF", fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
                    <span>🎁</span>
                    <span>Posting a verified question awards +10 Student Points</span>
                  </div>

                  <button
                    type="submit"
                    style={{
                      width: "100%",
                      padding: "12px",
                      background: "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
                      color: "#FFFFFF",
                      border: "none",
                      borderRadius: "10px",
                      fontSize: "13.5px",
                      fontWeight: 800,
                      cursor: "pointer",
                      boxShadow: "0 4px 12px rgba(37, 99, 235, 0.25)",
                      transition: "all 0.2s ease"
                    }}
                  >
                    Publish Question to Community 🚀
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* 2. ACADEMIC OVERVIEW & CANONICAL TIMELINE TAB */}
      {activeTab === "overview" && (
        <div className="academic-overview-panel fade-in" style={{ background: "#FFFFFF", padding: "24px", borderRadius: "14px", border: "1px solid #E2E8F0" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, color: "#0F172A" }}>📅 Academic Timeline & Live Countdowns</h2>
              <p style={{ fontSize: "13px", color: "#64748B", marginTop: "2px" }}>
                Single source of truth canonical events for {department || "All Departments"} • {academicYear || "All Years"}
              </p>
            </div>
            <button
              onClick={loadTimeline}
              style={{ padding: "6px 12px", background: "#F1F5F9", border: "1px solid #CBD5E1", borderRadius: "8px", fontSize: "12px", fontWeight: 700, cursor: "pointer" }}
            >
              🔄 Refresh Timeline
            </button>
          </div>

          {isLoadingTimeline ? (
            <div style={{ textAlign: "center", padding: "30px", color: "#64748B" }}>Loading campus timeline...</div>
          ) : timelineEvents.length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "14px" }}>
              {timelineEvents.map((evt) => {
                const nowMs = Date.now();
                const startMs = new Date(evt.start_datetime).getTime();
                const endMs = new Date(evt.end_datetime).getTime();
                let liveStatus = "UPCOMING";
                let liveLabel = "";

                if (nowMs >= startMs && nowMs <= endMs) {
                  liveStatus = "HAPPENING_NOW";
                  liveLabel = "LIVE NOW 🟢";
                } else if (nowMs > endMs) {
                  liveStatus = "EXPIRED";
                  liveLabel = "Ended ⚪";
                } else {
                  const diffSec = Math.floor((startMs - nowMs) / 1000);
                  const days = Math.floor(diffSec / 86400);
                  const hours = Math.floor((diffSec % 86400) / 3600);
                  const mins = Math.floor((diffSec % 3600) / 60);
                  const secs = diffSec % 60;

                  if (days >= 2) {
                    liveLabel = `${days} days remaining`;
                  } else if (days === 1) {
                    liveLabel = `1d ${hours}h ${mins}m remaining`;
                  } else if (hours >= 1) {
                    liveLabel = `${hours}h ${mins}m ${secs}s remaining`;
                  } else {
                    liveLabel = `${mins}m ${secs}s remaining ⏳`;
                  }
                }

                const cardBg = evt.priority === "URGENT" ? "#FFF5F5" : (evt.priority === "HIGH" ? "#EFF6FF" : "#F8FAFC");
                const cardBorder = evt.priority === "URGENT" ? "#FECACA" : (evt.priority === "HIGH" ? "#BFDBFE" : "#E2E8F0");
                const badgeColor = evt.priority === "URGENT" ? "#DC2626" : (evt.priority === "HIGH" ? "#2563EB" : "#475569");

                return (
                  <div key={evt.id} style={{ padding: "16px", background: cardBg, border: `1px solid ${cardBorder}`, borderRadius: "12px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                        <span style={{ fontSize: "11px", fontWeight: 800, color: badgeColor, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                          {evt.icon} {evt.priority} • {evt.category}
                        </span>
                        <span style={{ fontSize: "12px", fontWeight: 800, padding: "2px 8px", background: liveStatus === "HAPPENING_NOW" ? "#DC2626" : "#1E293B", color: "#FFFFFF", borderRadius: "10px" }}>
                          {liveLabel}
                        </span>
                      </div>

                      <h4 style={{ margin: "4px 0 4px 0", fontSize: "15px", color: "#0F172A", fontWeight: 800 }}>{evt.title}</h4>
                      <p style={{ margin: 0, fontSize: "12px", color: "#475569", lineHeight: 1.4 }}>{evt.description}</p>
                    </div>

                    <div style={{ marginTop: "12px", paddingTop: "8px", borderTop: "1px dashed #CBD5E1", fontSize: "11px", color: "#64748B", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span>📅 {evt.formatted_date}</span>
                      <span style={{ fontWeight: 700, color: "#2563EB" }}>Source: {evt.source}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "40px", color: "#64748B", fontSize: "13px" }}>
              No campus events scheduled for this academic selection.
            </div>
          )}
        </div>
      )}

      {/* 3. FACULTY TAB */}
      {activeTab === "faculty" && (
        <div className="faculty-panel fade-in" style={{ background: "#FFFFFF", padding: "24px", borderRadius: "14px", border: "1px solid #E2E8F0" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, color: "#0F172A" }}>👨‍🏫 Faculty Cabin & Room Directory</h2>
              <p style={{ fontSize: "13px", color: "#64748B" }}>Grounded in official <code>manipal_sce_faculty_cabins.csv</code> document</p>
            </div>
            <input
              type="text"
              placeholder="Search faculty name or cabin..."
              value={facultySearch}
              onChange={(e) => setFacultySearch(e.target.value)}
              style={{ padding: "8px 14px", borderRadius: "8px", border: "1px solid #CBD5E1", fontSize: "13px", width: "240px" }}
            />
          </div>

          {isLoadingFaculty ? (
            <div style={{ textAlign: "center", padding: "30px", color: "#64748B" }}>Loading faculty records...</div>
          ) : facultyList.length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "12px" }}>
              {facultyList.map((f, idx) => (
                <div key={idx} style={{ padding: "14px", border: "1px solid #E2E8F0", borderRadius: "10px", background: "#F8FAFC" }}>
                  <h4 style={{ margin: 0, fontSize: "14px", color: "#0F172A", fontWeight: 800 }}>{f.name}</h4>
                  <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#475569" }}>{f.designation} • {f.dept}</p>
                  <div style={{ marginTop: "8px", fontSize: "12px", color: "#166534", fontWeight: 700 }}>
                    🚪 Cabin: <code>{f.cabin}</code>
                  </div>
                  {f.email && <div style={{ fontSize: "11px", color: "#2563EB", marginTop: "2px" }}>📧 {f.email}</div>}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "40px", color: "#64748B", fontSize: "13px" }}>
              No faculty records found matching your search.
            </div>
          )}
        </div>
      )}

      {/* EDIT PROFILE MODAL */}
      {showEditProfileModal && (
        <div className="auth-overlay" onClick={() => setShowEditProfileModal(false)}>
          <div className="auth-modal-card fade-in" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "480px" }}>
            <div className="auth-modal-header">
              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 800 }}>Edit Profile & Academic Details</h3>
              <button className="modal-close-btn" onClick={() => setShowEditProfileModal(false)}>✕</button>
            </div>

            {profileSaveMsg && (
              <div style={{ padding: "8px 12px", borderRadius: "6px", fontSize: "12px", marginBottom: "10px", background: profileSaveMsg.startsWith("✓") ? "#F0FDF4" : "#FEF2F2", color: profileSaveMsg.startsWith("✓") ? "#166534" : "#991B1B" }}>
                {profileSaveMsg}
              </div>
            )}

            <form onSubmit={handleSaveProfile} className="auth-form" style={{ marginTop: "12px" }}>
              <div className="form-group">
                <label style={{ fontWeight: 700 }}>Verified Learner ID (Read-only):</label>
                <input type="text" disabled value={user?.learner_id || "N/A"} style={{ background: "#F1F5F9", color: "#64748B" }} />
              </div>

              <div className="form-group">
                <label style={{ fontWeight: 700 }}>Verified Registration Number (Read-only):</label>
                <input type="text" disabled value={user?.registration_number || "N/A"} style={{ background: "#F1F5F9", color: "#64748B" }} />
              </div>

              <div className="form-group">
                <label style={{ fontWeight: 700 }}>Extracted Admission Year (Read-only):</label>
                <input type="text" disabled value={user?.admission_year || "N/A"} style={{ background: "#F1F5F9", color: "#64748B" }} />
              </div>

              <div className="form-group">
                <label style={{ fontWeight: 700 }}>Branch / Department:</label>
                <select value={editDept} onChange={(e) => setEditDept(e.target.value)} style={{ width: "100%", padding: "8px", borderRadius: "6px", border: "1px solid #CBD5E1" }}>
                  {OFFICIAL_MIT_DEPARTMENTS.map((d) => (
                    <option key={d.code} value={d.name}>{d.name} ({d.code})</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label style={{ fontWeight: 700 }}>Current Academic Year:</label>
                <select value={editYear} onChange={(e) => setEditYear(e.target.value)} style={{ width: "100%", padding: "8px", borderRadius: "6px", border: "1px solid #CBD5E1" }}>
                  <option value="1st Year (2025-29)">1st Year (2025-29)</option>
                  <option value="2nd Year (2024-28)">2nd Year (2024-28)</option>
                  <option value="3rd Year (2023-27)">3rd Year (2023-27)</option>
                  <option value="4th Year (2022-26)">4th Year (2022-26)</option>
                </select>
              </div>

              <div className="form-group">
                <label style={{ fontWeight: 700 }}>Current Semester:</label>
                <select value={editSem} onChange={(e) => setEditSem(e.target.value)} style={{ width: "100%", padding: "8px", borderRadius: "6px", border: "1px solid #CBD5E1" }}>
                  <option value="Odd Semester (Jul - Dec)">Odd Semester (Jul - Dec)</option>
                  <option value="Even Semester (Jan - May)">Even Semester (Jan - May)</option>
                </select>
              </div>

              <div className="form-group">
                <label style={{ fontWeight: 700 }}>Bio:</label>
                <textarea rows={2} value={editBio} onChange={(e) => setEditBio(e.target.value)} placeholder="Short bio..." style={{ width: "100%", padding: "8px", borderRadius: "6px", border: "1px solid #CBD5E1" }} />
              </div>

              <div className="form-group">
                <label style={{ fontWeight: 700 }}>Skills:</label>
                <input type="text" value={editSkills} onChange={(e) => setEditSkills(e.target.value)} placeholder="e.g. Python, React, C++" />
              </div>

              <button type="submit" className="auth-submit-btn" disabled={profileSaveLoading} style={{ marginTop: "12px" }}>
                {profileSaveLoading ? "Saving..." : "Save Profile Changes 💾"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
