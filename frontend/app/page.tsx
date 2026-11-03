import Link from 'next/link'
import { ArrowUpRight, Bot, CalendarDays, ChevronRight, Compass, Heart, Search, Sparkles } from 'lucide-react'
import { buttonVariants } from '@/components/ui/button'
import { Logo } from '@/components/logo'

export default function LandingPage() {
  return (
    <main className="landing-shell">
      <nav className="landing-nav">
        <Logo />
        <div className="nav-links">
          <a href="#how">How it works</a>
          <a href="#explore">Explore</a>
          <a href="#about">About MITra</a>
        </div>
        <Link href="/login" className={buttonVariants({ variant: 'outline' })}>
          Sign in <ArrowUpRight data-icon="inline-end" />
        </Link>
      </nav>

      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow">
            <span className="eyebrow-dot" /> Made for MIT Manipal students
          </div>
          <h1>
            Your campus.
            <br />
            <em>Your companion.</em>
          </h1>
          <p>
            Meet MITra — the intelligent campus companion that helps you find answers, discover
            opportunities, and make the most of your time at Manipal.
          </p>
          <div className="hero-actions">
            <Link href="/login" className={buttonVariants({ size: 'lg' })}>
              Open MITra <ArrowUpRight data-icon="inline-end" />
            </Link>
            <a className="text-button" href="#how">
              See how it works <ChevronRight />
            </a>
          </div>
          <div className="trust-row">
            <div className="avatar-stack">
              <span>AS</span>
              <span>RK</span>
              <span>MN</span>
              <span>+</span>
            </div>
            <span>Built for the MIT Manipal community</span>
          </div>
        </div>
        <div className="hero-orbit" aria-hidden="true">
          <div className="orbit-ring ring-one" />
          <div className="orbit-ring ring-two" />
          <div className="orbit-core">
            <Sparkles />
            <span>
              Ask me
              <br />
              anything
            </span>
          </div>
          <div className="orbit-chip chip-one">
            <Search />
            <span>Campus search</span>
          </div>
          <div className="orbit-chip chip-two">
            <CalendarDays />
            <span>Never miss a thing</span>
          </div>
          <div className="orbit-chip chip-three">
            <Heart />
            <span>Just for you</span>
          </div>
        </div>
      </section>

      <section className="feature-strip" id="how">
        <div>
          <span className="feature-number">01</span>
          <Bot />
          <h3>Ask anything</h3>
          <p>Grounded answers for campus life, academics and beyond.</p>
        </div>
        <div>
          <span className="feature-number">02</span>
          <Compass />
          <h3>Find your people</h3>
          <p>Clubs, projects and opportunities that fit your interests.</p>
        </div>
        <div>
          <span className="feature-number">03</span>
          <Sparkles />
          <h3>Make it yours</h3>
          <p>A smarter student experience that learns what matters to you.</p>
        </div>
      </section>

      <section className="landing-bottom" id="explore">
        <div>
          <p className="section-kicker">ONE PLACE FOR CAMPUS LIFE</p>
          <h2>
            Less searching.
            <br />
            <span>More doing.</span>
          </h2>
        </div>
        <div className="mini-stat">
          <strong>24/7</strong>
          <span>Your campus companion, whenever you need it.</span>
        </div>
        <div className="mini-stat">
          <strong>∞</strong>
          <span>Possibilities to explore, learn and connect.</span>
        </div>
      </section>

      <section className="landing-static" id="about">
        <h3>About MITra</h3>
        <p>
          MITra is an AI-powered campus companion built by and for MIT Manipal students — one
          place to ask questions, discover opportunities, and stay on top of campus life.
        </p>
      </section>
      <section className="landing-static" id="privacy">
        <h3>Privacy</h3>
        <p>
          MITra only uses your activity to personalize recommendations you can see and control
          from Settings. You can reset or disable personalization at any time.
        </p>
      </section>
      <section className="landing-static" id="help">
        <h3>Help</h3>
        <p>Need a hand? Reach the MITra team at help@mitra.manipal.edu once you&apos;re signed in, or ask MITra directly from the chat.</p>
      </section>
      <section className="landing-static" id="feedback">
        <h3>Feedback</h3>
        <p>Spotted something off or have an idea? Send it to feedback@mitra.manipal.edu — we read every message.</p>
      </section>

      <footer className="landing-footer">
        <Logo />
        <span>© 2026 MITra · MIT Manipal</span>
        <div>
          <a href="#privacy">Privacy</a>
          <a href="#help">Help</a>
          <a href="#feedback">Feedback</a>
        </div>
      </footer>
    </main>
  )
}
