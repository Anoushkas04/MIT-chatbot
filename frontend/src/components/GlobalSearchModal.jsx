import React, { useState, useEffect } from "react";
import { performGlobalSearch } from "../api";

export default function GlobalSearchModal({ isOpen, onClose, onAskCopilot, initialQuery = "" }) {
  const [query, setQuery] = useState(initialQuery);
  const [category, setCategory] = useState("all");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [counts, setCounts] = useState({ official: 0, community: 0, total: 0 });

  useEffect(() => {
    if (isOpen) {
      setQuery(initialQuery);
      executeSearch(initialQuery, category);
    }
  }, [isOpen, initialQuery, category]);

  const executeSearch = async (qText, catFilter) => {
    setLoading(true);
    const data = await performGlobalSearch(qText, catFilter);
    if (data && data.results) {
      setResults(data.results);
      setCounts({
        official: data.official_count || 0,
        community: data.community_count || 0,
        total: data.total_results || 0,
      });
    } else {
      setResults([]);
    }
    setLoading(false);
  };

  if (!isOpen) return null;

  const categories = [
    { id: "all", label: "🌐 All Domains" },
    { id: "official", label: "🟢 Official Docs & Policies" },
    { id: "community", label: "💬 Community Posts & Hacks" },
    { id: "Academic Information", label: "📅 Academic Calendar & Cutoffs" },
    { id: "Events", label: "🎪 Events & Notices" },
  ];

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="rewards-modal-card fade-in" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "780px", padding: "24px" }}>
        {/* Header Search Box */}
        <div className="search-modal-input-wrap">
          <span className="search-modal-icon">🔍</span>
          <input
            type="text"
            className="search-modal-input"
            placeholder="Search official PDFs, cutoffs, student posts, mess tips, events..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              executeSearch(e.target.value, category);
            }}
            autoFocus
          />
          <button className="auth-close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Domain Filter Tabs */}
        <div className="sub-community-bar" style={{ marginTop: "12px" }}>
          {categories.map((cat) => (
            <button
              key={cat.id}
              className={`sub-channel-btn ${category === cat.id ? "active" : ""}`}
              onClick={() => setCategory(cat.id)}
            >
              <span>{cat.label}</span>
            </button>
          ))}
        </div>

        {/* Results Metadata Summary Bar */}
        <div className="search-meta-bar">
          <span className="search-meta-text">
            Found <strong>{counts.total}</strong> results
            {query ? ` for "${query}"` : ""} • 🟢 <strong>{counts.official}</strong> Official Facts, 🟡 <strong>{counts.community}</strong> Community Insights
          </span>
        </div>

        {/* Results List */}
        <div className="search-results-container">
          {loading ? (
            <div className="search-loading-text">⚡ Executing dual-knowledge search query...</div>
          ) : results.length > 0 ? (
            results.map((item) => (
              <div key={item.id} className={`search-result-card ${item.source_type}`}>
                <div className="result-card-header">
                  <span className={`result-source-pill ${item.source_type}`}>{item.badge}</span>
                  <span className="result-category">{item.category}</span>
                  {item.relevance && <span className="result-relevance">Match Score: {(item.relevance * 100).toFixed(0)}%</span>}
                </div>

                <h4 className="result-title">{item.title}</h4>
                <p className="result-snippet">"{item.snippet}"</p>

                <div className="result-card-foot">
                  <span className="result-target">Target: {item.link_target}</span>
                  <button
                    className="result-action-btn"
                    onClick={() => {
                      onClose();
                      onAskCopilot && onAskCopilot(item.title);
                    }}
                  >
                    Ask AI Copilot 🤖
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="no-search-results">No matching documents or community posts found for "{query}".</div>
          )}
        </div>

        {/* Footer */}
        <div className="inspector-footer" style={{ marginTop: "12px" }}>
          <span className="footer-note">MIT CampusOS Global Search • Dual Knowledge Partition (🟢 Official vs 🟡 Community)</span>
        </div>
      </div>
    </div>
  );
}
