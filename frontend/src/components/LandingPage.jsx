import Logo from "./Logo";
import "./LandingPage.css";

const features = [
  {
    num: "01",
    icon: "🤖",
    title: "Ask anything",
    desc: "Grounded answers for campus life, academics, syllabi, faculty and beyond.",
  },
  {
    num: "02",
    icon: "🧭",
    title: "Find your people",
    desc: "Clubs, events and opportunities curated for MIT Manipal students.",
  },
  {
    num: "03",
    icon: "✦",
    title: "Make it yours",
    desc: "A smarter student experience powered by the MIT Manipal community.",
  },
];

export default function LandingPage({ onEnter }) {
  return (
    <main className="lp-shell">
      {/* Nav */}
      <nav className="lp-nav">
        <Logo />
        <div className="lp-nav-links">
          <a href="#how">How it works</a>
          <a href="#about">About MITra</a>
        </div>
        <button className="lp-btn-outline" onClick={onEnter}>
          Sign in <span className="lp-arrow">↗</span>
        </button>
      </nav>

      {/* Hero */}
      <section className="lp-hero">
        <div className="lp-hero-copy">
          <div className="lp-eyebrow">
            <span className="lp-eyebrow-dot" />
            Made for MIT Manipal students
          </div>
          <h1 className="lp-h1">
            Your campus.<br />
            <em>Your companion.</em>
          </h1>
          <p className="lp-hero-p">
            Meet MITra — the intelligent campus companion that helps you find
            answers, discover opportunities, and make the most of your time at
            Manipal.
          </p>
          <div className="lp-hero-actions">
            <button className="lp-btn-primary" onClick={onEnter}>
              Open MITra <span className="lp-arrow">↗</span>
            </button>
            <button
              className="lp-text-btn"
              onClick={() =>
                document.getElementById("how")?.scrollIntoView({ behavior: "smooth" })
              }
            >
              See how it works <span style={{ fontSize: 13 }}>›</span>
            </button>
          </div>
          <div className="lp-trust-row">
            <div className="lp-avatar-stack">
              <span>AS</span>
              <span>RK</span>
              <span>MN</span>
              <span>+</span>
            </div>
            <span>Built for the MIT Manipal community</span>
          </div>
        </div>

        {/* Orbit illustration */}
        <div className="lp-orbit" aria-hidden="true">
          <div className="lp-ring lp-ring-1" />
          <div className="lp-ring lp-ring-2" />
          <div className="lp-orbit-core">
            <span style={{ fontSize: 22 }}>✦</span>
            <span>Ask me<br />anything</span>
          </div>
          <div className="lp-chip lp-chip-1">
            <span>🔍</span>
            <span>Campus search</span>
          </div>
          <div className="lp-chip lp-chip-2">
            <span>📅</span>
            <span>Never miss a thing</span>
          </div>
          <div className="lp-chip lp-chip-3">
            <span>💬</span>
            <span>Community answers</span>
          </div>
        </div>
      </section>

      {/* Feature strip */}
      <section className="lp-feature-strip" id="how">
        {features.map((f) => (
          <div key={f.num} className="lp-feature">
            <span className="lp-feature-num">{f.num}</span>
            <span className="lp-feature-icon">{f.icon}</span>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Stats strip */}
      <section className="lp-stats" id="about">
        <div className="lp-stats-copy">
          <p className="lp-kicker">ONE PLACE FOR CAMPUS LIFE</p>
          <h2 className="lp-stats-h2">
            Less searching.<br />
            <span>More doing.</span>
          </h2>
        </div>
        <div className="lp-mini-stat">
          <strong>24/7</strong>
          <span>Your campus companion, whenever you need it.</span>
        </div>
        <div className="lp-mini-stat">
          <strong>∞</strong>
          <span>Possibilities to explore, learn and connect.</span>
        </div>
      </section>

      {/* Footer */}
      <footer className="lp-footer">
        <Logo size="sm" />
        <span>© 2026 MITra · MIT Manipal</span>
        <div className="lp-footer-links">
          <a href="#privacy">Privacy</a>
          <a href="#help">Help</a>
          <a href="#feedback">Feedback</a>
        </div>
      </footer>
    </main>
  );
}
