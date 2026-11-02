'use client'

import { useEffect, useState } from 'react'
import { AlertCircle, ArrowUpRight, Bell, CalendarDays, Search, Send, Sparkles } from 'lucide-react'
import { getNotifications, getTimeline, type NotificationsResponse, type TimelineEvent } from '@/lib/api'

export function HomeView({ setActive }: { setActive: (view: string) => void }) {
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [notifications, setNotifications] = useState<NotificationsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getTimeline(), getNotifications()])
      .then(([timeline, alerts]) => { setEvents(timeline.events); setNotifications(alerts) })
      .catch(reason => setError(reason instanceof Error ? reason.message : 'Dashboard data could not be loaded.'))
      .finally(() => setLoading(false))
  }, [])

  const activeEvents = events.filter(event => event.status !== 'EXPIRED')
  return <div className="view"><div className="view-header"><div><p className="section-kicker">GUEST WORKSPACE · LIVE DATA</p><h1>Welcome to MITra <span>✦</span></h1><p className="view-sub">Your public campus timeline is supplied by CampusOS.</p></div><div className="header-actions"><button className="icon-button" onClick={() => setActive('Planner')} aria-label={`${notifications?.unread_count ?? 0} unread notifications`}><Bell />{!!notifications?.unread_count && <i />}</button><div className="header-avatar">G</div></div></div>
    <button className="search-bar" onClick={() => setActive('Search')}><Search /><span>Search live campus sources…</span><kbd>Open</kbd></button>
    {error && <div className="inline-error"><AlertCircle /> {error}</div>}
    <div className="home-grid"><section className="ask-card"><div className="ask-glow" /><div className="ask-content"><div className="ai-avatar"><Sparkles /></div><p className="section-kicker">YOUR AI CAMPUS COMPANION</p><h2>What’s on your mind?</h2><p>Ask a question and inspect the evidence used in the answer.</p><button className="ask-input" onClick={() => setActive('Ask MITra')}><span>Ask MITra anything…</span><Send /></button></div></section>
      <section className="today-card"><div className="card-heading"><div><p className="section-kicker">CANONICAL TIMELINE</p><h3>What’s coming up</h3></div><button onClick={() => setActive('Planner')}>View planner <ArrowUpRight /></button></div>
        {loading && <p className="loading-copy">Loading official events…</p>}
        {!loading && activeEvents.length === 0 && <div className="empty-state compact"><CalendarDays /><p>No upcoming published events.</p></div>}
        <div className="timeline">{activeEvents.slice(0, 3).map(event => <div key={event.id}><time>{new Date(event.start_datetime).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</time><span className="timeline-line blue-line" /><article><strong>{event.title}</strong><span>{event.countdown_label} · {event.source}</span></article></div>)}</div>
      </section></div>
    <div className="section-row"><div><p className="section-kicker">FROM THE LIVE CALENDAR</p><h2>Worth a look</h2></div><button className="link-button" onClick={() => setActive('Search')}>Search all sources <ArrowUpRight /></button></div>
    {!loading && events.length === 0 && <div className="empty-state"><CalendarDays /><h3>No discoveries to show yet</h3><p>Published campus events will appear here automatically.</p></div>}
    <div className="discovery-grid">{activeEvents.slice(0, 3).map(event => <article className="discovery-card blue" key={event.id}><div className="discovery-top"><span className="discovery-icon">{event.icon}</span></div><span className="pill">{event.category}</span><h3>{event.title}</h3><p>{event.formatted_date}</p><div className="why"><Sparkles /> {event.time_string}</div></article>)}</div>
    {!!notifications?.notifications.length && <section className="live-notices"><p className="section-kicker">ACTIVE NOTICES</p>{notifications.notifications.slice(0, 3).map(notice => <article key={notice.state_id}><Bell /><div><strong>{notice.title}</strong><p>{notice.content}</p><small>{notice.source_doc}</small></div></article>)}</section>}
  </div>
}
