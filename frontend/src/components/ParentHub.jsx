import React, { useState, useEffect } from "react";
import { fetchCutoffRanks } from "../api";

export default function ParentHub({ onPromptSelect }) {
  const [course, setCourse] = useState("B.Tech");
  const [userRank, setUserRank] = useState("");
  const [cutoffs, setCutoffs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCutoffs();
  }, [course]);

  const loadCutoffs = async () => {
    setLoading(true);
    const res = await fetchCutoffRanks(course);
    if (res && res.cutoffs) {
      setCutoffs(res.cutoffs);
    } else {
      // Fallback
      setCutoffs([
        { program: "Computer Science & Engineering (CSE)", round1: 1620, round2: 1845, round3: 1950, degree: "B.Tech" },
        { program: "AI & Machine Learning (AIML)", round1: 2110, round2: 2390, round3: 2510, degree: "B.Tech" },
        { program: "Information Technology (IT)", round1: 3150, round2: 3520, round3: 3710, degree: "B.Tech" },
        { program: "Data Science & Engineering", round1: 3890, round2: 4350, round3: 4620, degree: "B.Tech" },
        { program: "Electronics & Communication (ECE)", round1: 5120, round2: 5890, round3: 6240, degree: "B.Tech" },
        { program: "Electrical & Electronics (EEE)", round1: 9210, round2: 10450, round3: 11200, degree: "B.Tech" },
        { program: "Mechanical Engineering", round1: 18500, round2: 21300, round3: 22800, degree: "B.Tech" },
      ]);
    }
    setLoading(false);
  };

  const parsedRank = parseInt(userRank, 10);

  return (
    <div className="workspace-container fade-in">
      {/* Header */}
      <div className="workspace-header">
        <div className="header-left">
          <div className="header-badge badge-teal">🏛️ Campus Info Hub</div>
          <h1 className="header-title">Admissions, Cutoff Ranks & Campus Policy Hub</h1>
          <p className="header-desc">
            Explore verified counseling cutoff ranks (Rounds 1–3), tuition/hostel fee breakdowns, and parent guidelines for MIT Manipal (MAHE).
          </p>
        </div>
      </div>

      {/* Interactive Rank Eligibility Calculator */}
      <div className="section-card cutoff-calculator-card">
        <div className="calc-header">
          <h3>🎯 Interactive Cutoff Rank & Eligibility Checker</h3>
          <p>Enter your MET Rank to calculate program eligibility across counseling rounds:</p>
        </div>

        <div className="calc-form">
          <div className="form-group flex-1">
            <label>Select Degree Program:</label>
            <select value={course} onChange={(e) => setCourse(e.target.value)}>
              <option value="B.Tech">B.Tech (Undergraduate)</option>
              <option value="M.Tech">M.Tech (Postgraduate)</option>
              <option value="M.Pharm">M.Pharm (Pharmacy)</option>
            </select>
          </div>

          <div className="form-group flex-1">
            <label>Enter Your MET Entrance Rank (Optional):</label>
            <input
              type="number"
              placeholder="e.g. 2500"
              value={userRank}
              onChange={(e) => setUserRank(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Cutoffs Visual Table */}
      <div className="section-card">
        <div className="card-header">
          <h3>📊 Verified Cutoff Rank Directory ({course})</h3>
          <span className="badge-outline">MAHE Counseling 2026</span>
        </div>

        {loading ? (
          <div className="loading-spinner">Loading official cutoffs...</div>
        ) : (
          <div className="table-responsive">
            <table className="cutoff-table">
              <thead>
                <tr>
                  <th>Academic Program</th>
                  <th>Round 1 Cutoff</th>
                  <th>Round 2 Cutoff</th>
                  <th>Round 3 Cutoff</th>
                  {parsedRank > 0 && <th>Rank Status ({parsedRank})</th>}
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {cutoffs.map((item, idx) => {
                  const eligibleRound2 = parsedRank > 0 && parsedRank <= item.round2;
                  const eligibleRound3 = parsedRank > 0 && parsedRank <= item.round3;

                  return (
                    <tr key={idx}>
                      <td className="program-name">{item.program}</td>
                      <td><span className="rank-tag">Rank {item.round1}</span></td>
                      <td><span className="rank-tag">Rank {item.round2}</span></td>
                      <td><span className="rank-tag">Rank {item.round3}</span></td>
                      {parsedRank > 0 && (
                        <td>
                          {eligibleRound2 ? (
                            <span className="eligibility-pill pass">High Chance (Eligible R2)</span>
                          ) : eligibleRound3 ? (
                            <span className="eligibility-pill maybe">Possible (Round 3)</span>
                          ) : (
                            <span className="eligibility-pill fail">Rank Exceeded</span>
                          )}
                        </td>
                      )}
                      <td>
                        <button
                          className="table-ai-btn"
                          onClick={() =>
                            onPromptSelect(
                              `What are the admission prospects, fee structure, and cutoffs for ${item.program} at MIT Manipal?`
                            )
                          }
                        >
                          Ask AI
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Parent Guides Grid */}
      <div className="two-col-grid">
        <div className="section-card">
          <h3>💰 Fee Structure & Payment Timelines</h3>
          <ul className="info-list">
            <li><strong>B.Tech Tuition Fee:</strong> ₹3.35 Lakhs - ₹4.10 Lakhs per annum depending on branch.</li>
            <li><strong>Hostel & Mess Charges:</strong> ₹1.25 Lakhs - ₹1.80 Lakhs per year (AC / Non-AC options).</li>
            <li><strong>Caution Deposit:</strong> ₹10,000 (Refundable upon degree completion).</li>
          </ul>
          <button
            className="card-action-btn"
            onClick={() => onPromptSelect("Provide a complete breakdown of hostel options, mess fee structure, and payment deadlines for 1st year students.")}
          >
            🤖 Ask AI for Complete Fee Breakdown →
          </button>
        </div>

        <div className="section-card">
          <h3>🛡️ Campus Safety, Medical & Hostel Rules</h3>
          <ul className="info-list">
            <li><strong>Curfew & Campus Entry:</strong> 10:00 PM hostel in-time strictly enforced for first-year students.</li>
            <li><strong>Kasturba Hospital (KH) Access:</strong> Free outpatient medical consultation for MAHE students.</li>
            <li><strong>Anti-Ragging Zero Tolerance:</strong> 24/7 Helpline & Campus Proctorial Board oversight.</li>
          </ul>
          <button
            className="card-action-btn"
            onClick={() => onPromptSelect("What are the hostel curfew rules, campus medical facilities, and leave application procedures for parents?")}
          >
            🤖 Ask AI for Parent Guidelines →
          </button>
        </div>
      </div>
    </div>
  );
}
