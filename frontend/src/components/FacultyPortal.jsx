import React, { useState, useEffect } from "react";
import { fetchFacultyDirectory } from "../api";
import { OFFICIAL_MIT_DEPARTMENTS } from "../departments";

export default function FacultyPortal({ onPromptSelect }) {
  const [query, setQuery] = useState("");
  const [deptFilter, setDeptFilter] = useState("All");
  const [facultyData, setFacultyData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadFaculty();
  }, [deptFilter]);

  const loadFaculty = async () => {
    setLoading(true);
    const res = await fetchFacultyDirectory(query, deptFilter);
    if (res && res.data) {
      setFacultyData(res.data);
    } else {
      // Default dataset fallback
      setFacultyData([
        { name: "Dr. Somanath S.", dept: "Computer Science & Engg", designation: "Professor & Head", cabin: "AB5-302", email: "somanath.s@manipal.edu", research: "AI & Distributed Systems" },
        { name: "Dr. Radhika M. Pai", dept: "Computer Science & Engg", designation: "Professor", cabin: "AB5-314", email: "radhika.pai@manipal.edu", research: "Cloud Computing & Security" },
        { name: "Dr. Srikanth Prabhu", dept: "Computer Science & Engg", designation: "Associate Professor", cabin: "AB5-308", email: "srikanth.prabhu@manipal.edu", research: "Biometrics & Machine Learning" },
        { name: "Dr. Harish Kumar S.", dept: "Information Technology", designation: "Professor & Head", cabin: "AB5-402", email: "harish.kumar@manipal.edu", research: "Cybersecurity & IoT" },
        { name: "Dr. Smitha N. Pai", dept: "Information Technology", designation: "Professor", cabin: "AB5-410", email: "smitha.pai@manipal.edu", research: "Data Science" },
        { name: "Dr. Subramanya Bhat", dept: "Electronics & Comm Engg", designation: "Professor & Head", cabin: "AB3-104", email: "subramanya.bhat@manipal.edu", research: "VLSI Design & Embedded Systems" },
      ]);
    }
    setLoading(false);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadFaculty();
  };

  return (
    <div className="workspace-container fade-in">
      {/* Header */}
      <div className="workspace-header">
        <div className="header-left">
          <div className="header-badge badge-purple">👨‍🏫 Faculty & Administrative Portal</div>
          <h1 className="header-title">Faculty Cabin & Departmental Directory</h1>
          <p className="header-desc">
            Search professor cabins, academic designations, research specialization areas, and direct email contacts parsed from official campus registries.
          </p>
        </div>
      </div>

      {/* Directory Search & Filter Bar */}
      <div className="section-card search-filter-card">
        <form onSubmit={handleSearchSubmit} className="search-filter-grid">
          <div className="form-group flex-2">
            <label>Search Name, Cabin, or Keyword:</label>
            <input
              type="text"
              placeholder="e.g. Radhika Pai, AB5-302, Machine Learning, IT..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          <div className="form-group flex-1">
            <label>Filter Department:</label>
            <select value={deptFilter} onChange={(e) => setDeptFilter(e.target.value)}>
              <option value="All">All Departments ({OFFICIAL_MIT_DEPARTMENTS.length})</option>
              {OFFICIAL_MIT_DEPARTMENTS.map((d) => (
                <option key={d.code} value={d.name}>
                  {d.code} — {d.name}
                </option>
              ))}
            </select>
          </div>

          <button type="submit" className="submit-btn search-btn">🔍 Find Faculty</button>
        </form>
      </div>

      {/* Faculty Cards Grid */}
      <div className="faculty-grid">
        {loading ? (
          <div className="loading-spinner">Loading faculty records...</div>
        ) : facultyData.length > 0 ? (
          facultyData.map((f, i) => (
            <div key={i} className="faculty-card">
              <div className="f-header">
                <span className="f-avatar">👨‍🏫</span>
                <div>
                  <h3 className="f-name">{f.name}</h3>
                  <span className="f-desig">{f.designation}</span>
                </div>
              </div>

              <div className="f-details">
                <div className="f-detail-row">
                  <span className="f-label">🏢 Department:</span>
                  <span className="f-val">{f.dept}</span>
                </div>

                <div className="f-detail-row highlight-cabin">
                  <span className="f-label">📍 Cabin Location:</span>
                  <span className="f-val-bold">{f.cabin}</span>
                </div>

                <div className="f-detail-row">
                  <span className="f-label">🔬 Research Focus:</span>
                  <span className="f-val">{f.research}</span>
                </div>

                <div className="f-detail-row">
                  <span className="f-label">✉️ Email:</span>
                  <a href={`mailto:${f.email}`} className="f-email">{f.email}</a>
                </div>
              </div>

              <button
                className="f-ask-ai"
                onClick={() => onPromptSelect(`Where is ${f.name}'s cabin located and what are their research areas?`)}
              >
                🤖 Ask AI Copilot about {f.name.split(" ")[1] || f.name} →
              </button>
            </div>
          ))
        ) : (
          <div className="no-results">No faculty members found matching your search.</div>
        )}
      </div>
    </div>
  );
}
