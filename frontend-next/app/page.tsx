'use client'

import { useState, type ReactNode } from 'react'
import {
  ArrowUpRight,
  Bell,
  Bot,
  CalendarDays,
  ChevronRight,
  Compass,
  Heart,
  LayoutDashboard,
  Menu,
  MessageCircle,
  MoreHorizontal,
  Search,
  Settings,
  Sparkles,
  Users,
  Zap,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ConnectionStatus } from '@/components/system/connection-status'
import { ChatView } from '@/components/chat/chat-view'
import { HomeView } from '@/components/dashboard/home-view'
import { SearchView } from '@/components/search/search-view'
import { CommunityView } from '@/components/community/community-view'
import { DirectoryView } from '@/components/directory/directory-view'
import { DiscoverView } from '@/components/discover/discover-view'
import { PlannerView } from '@/components/planner/planner-view'
import { UtilityView } from '@/components/utilities/utility-view'

const navItems = [
  { label: 'Home', icon: LayoutDashboard },
  { label: 'Ask MITra', icon: MessageCircle },
  { label: 'Discover', icon: Compass },
  { label: 'Community', icon: Users },
  { label: 'Directory', icon: Search },
  { label: 'Planner', icon: CalendarDays },
  { label: 'Utilities', icon: Zap },
]

function Logo({ light = false }: { light?: boolean }) {
  return <div className={`brand ${light ? 'brand-light' : ''}`}><span className="brand-mark">M</span><span>MIT<span className="brand-accent">ra</span></span></div>
}

function Landing({ onEnter }: { onEnter: () => void }) {
  return (
    <main className="landing-shell">
      <nav className="landing-nav"><Logo /><div className="nav-links"><a href="#how">How it works</a><a href="#explore">Explore</a><a href="#about">About MITra</a></div><Button variant="outline" onClick={onEnter}>Open guest workspace <ArrowUpRight data-icon="inline-end" /></Button></nav>
      <section className="hero">
        <div className="hero-copy"><div className="eyebrow"><span className="eyebrow-dot" /> Made for MIT Manipal students</div><h1>Your campus.<br /><em>Your companion.</em></h1><p>Meet MITra — the intelligent campus companion that helps you find answers, discover opportunities, and make the most of your time at Manipal.</p><div className="hero-actions"><Button size="lg" onClick={onEnter}>Open MITra <ArrowUpRight data-icon="inline-end" /></Button><button className="text-button" onClick={() => document.getElementById('how')?.scrollIntoView({ behavior: 'smooth' })}>See how it works <ChevronRight /></button></div><div className="trust-row"><div className="avatar-stack"><span>AS</span><span>RK</span><span>MN</span><span>+</span></div><span>Built for the MIT Manipal community</span></div></div>
        <div className="hero-orbit" aria-hidden="true"><div className="orbit-ring ring-one" /><div className="orbit-ring ring-two" /><div className="orbit-core"><Sparkles /><span>Ask me<br />anything</span></div><div className="orbit-chip chip-one"><Search /><span>Campus search</span></div><div className="orbit-chip chip-two"><CalendarDays /><span>Never miss a thing</span></div><div className="orbit-chip chip-three"><Heart /><span>Just for you</span></div></div>
      </section>
      <section className="feature-strip" id="how"><div><span className="feature-number">01</span><Bot /><h3>Ask anything</h3><p>Grounded answers for campus life, academics and beyond.</p></div><div><span className="feature-number">02</span><Compass /><h3>Find your people</h3><p>Clubs, projects and opportunities that fit your interests.</p></div><div><span className="feature-number">03</span><Sparkles /><h3>Make it yours</h3><p>A smarter student experience that learns what matters to you.</p></div></section>
      <section className="landing-bottom" id="explore"><div><p className="section-kicker">ONE PLACE FOR CAMPUS LIFE</p><h2>Less searching.<br /><span>More doing.</span></h2></div><div className="mini-stat"><strong>24/7</strong><span>Your campus companion, whenever you need it.</span></div><div className="mini-stat"><strong>∞</strong><span>Possibilities to explore, learn and connect.</span></div></section>
      <footer className="landing-footer"><Logo /><span>© 2026 MITra · MIT Manipal</span><div><a href="#privacy">Privacy</a><a href="#help">Help</a><a href="#feedback">Feedback</a></div></footer>
    </main>
  )
}

function GuestGate({ onBack, onContinue }: { onBack: () => void; onContinue: () => void }) {
  return <main className="auth-shell"><button className="auth-back" onClick={onBack}>← Back to MITra</button><div className="auth-card guest-card"><div className="auth-brand"><Logo /><span className="auth-orb"><Sparkles /></span></div><p className="section-kicker">GUEST PREVIEW</p><h1>Explore the integration safely.</h1><p className="auth-sub">Authentication is intentionally outside this integration batch. Guest mode lets you review the new experience without creating a fake account or session.</p><div className="guest-notice"><Bot /><div><strong>Guest access</strong><span>Public campus features are available. Identity-dependent and protected actions will remain unavailable until authentication is handled separately.</span></div></div><Button className="auth-submit" size="lg" onClick={onContinue}>Continue as guest <ArrowUpRight data-icon="inline-end" /></Button><p className="auth-legal">No credentials or personal data are collected in guest mode.</p></div><div className="auth-side"><div className="quote-mark">“</div><blockquote>A working integration starts with honest system boundaries.</blockquote><span>— MITra integration preview</span><div className="auth-side-dots"><i /><i /><i /></div></div></main>
}

function Sidebar({ active, setActive, onLogout }: { active: string; setActive: (v: string) => void; onLogout: () => void }) {
  return <aside className="sidebar"><div className="sidebar-top"><Logo /><button className="mobile-menu"><Menu /></button></div><div className="profile-mini"><div className="profile-avatar">G</div><div><strong>Guest</strong><span>Integration preview</span></div><MoreHorizontal /></div><nav className="side-nav">{navItems.map(item => <button key={item.label} className={active === item.label ? 'active' : ''} onClick={() => setActive(item.label)}><item.icon /><span>{item.label}</span>{item.label === 'Ask MITra' && <span className="nav-badge">Preview</span>}</button>)}</nav><div className="sidebar-section"><span className="side-label">SAVED</span><button onClick={() => setActive('Discover')}><Heart /><span>Saved for later</span><small>Local</small></button><button onClick={() => setActive('Planner')}><Bell /><span>Notifications</span><small className="alert-dot" /></button></div><div className="sidebar-bottom"><ConnectionStatus /><button onClick={() => setActive('Settings')}><Settings /><span>Settings</span></button><button onClick={onLogout}><span className="profile-avatar small">G</span><span>Exit guest mode</span><ArrowUpRight /></button></div></aside>
}



function SettingsView() { return <div className="view settings-view"><div className="view-header"><div><p className="section-kicker">GUEST SETTINGS</p><h1>Preview preferences.</h1><p className="view-sub">Guest preferences are local-only until identity features are integrated separately.</p></div></div><div className="settings-list"><section><h3>Profile</h3><div className="settings-card profile-setting"><div className="header-avatar large">G</div><div><strong>Guest</strong><span>No account connected</span><small>Integration preview workspace</small></div><button disabled>Unavailable in guest mode</button></div></section><section><h3>Personalization preview</h3><div className="settings-card"><div><strong>Behavioral personalization</strong><span>Requires a signed-in profile and is intentionally disabled.</span></div><button className="toggle" disabled><i /></button></div><div className="settings-card"><div><strong>Show inferred interests</strong><span>No interests are inferred or stored for guests.</span></div><button className="toggle" disabled><i /></button></div></section><section><h3>Notifications</h3><div className="settings-card"><div><strong>Public campus updates</strong><span>Live published notices are available in the Planner. Personal notification preferences require sign-in.</span></div><button className="toggle" disabled><i /></button></div></section></div></div> }

function Workspace({ onLogout }: { onLogout: () => void }) {
  const [active, setActive] = useState('Home')
  const views: Record<string, ReactNode> = {
    Home: <HomeView setActive={setActive} />,
    'Ask MITra': <ChatView />,
    Search: <SearchView />,
    Discover: <DiscoverView />,
    Community: <CommunityView />,
    Directory: <DirectoryView />,
    Utilities: <UtilityView setActive={setActive} />,
    Planner: <PlannerView />,
    Settings: <SettingsView />,
  }
  return <main className="workspace"><Sidebar active={active} setActive={setActive} onLogout={onLogout} /><div className="workspace-main"><div className="mobile-top"><Logo /><button><Menu /></button></div>{views[active] ?? views.Home}</div></main>
}

export default function Page() { const [screen, setScreen] = useState<'landing' | 'guest' | 'workspace'>('landing'); if (screen === 'guest') return <GuestGate onBack={() => setScreen('landing')} onContinue={() => setScreen('workspace')} />; if (screen === 'workspace') return <Workspace onLogout={() => setScreen('landing')} />; return <Landing onEnter={() => setScreen('guest')} /> }
