'use client'

import { useEffect, useMemo, useState } from 'react'
import { AlertCircle, CalendarDays, ChevronLeft, ChevronRight, LockKeyhole } from 'lucide-react'
import { getNotifications, getTimeline, type CampusNotification, type TimelineEvent } from '@/lib/api'

export function PlannerView() {
  const [cursor, setCursor] = useState(() => new Date())
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [notices, setNotices] = useState<CampusNotification[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  useEffect(() => { Promise.all([getTimeline(), getNotifications()]).then(([timeline, notifications]) => { setEvents(timeline.events); setNotices(notifications.notifications) }).catch(reason => setError(reason instanceof Error ? reason.message : 'Planner data failed to load.')).finally(() => setLoading(false)) }, [])

  const year = cursor.getFullYear(), month = cursor.getMonth()
  const days = useMemo(() => {
    const leading = (new Date(year, month, 1).getDay() + 6) % 7
    const count = new Date(year, month + 1, 0).getDate()
    return [...Array.from({ length: leading }, () => null), ...Array.from({ length: count }, (_, index) => index + 1)]
  }, [year, month])
  const eventDays = new Set(events.filter(event => { const date = new Date(event.start_datetime); return date.getFullYear() === year && date.getMonth() === month }).map(event => new Date(event.start_datetime).getDate()))
  const today = new Date()

  return <div className="view"><div className="view-header"><div><p className="section-kicker">LIVE ACADEMIC PLANNER</p><h1>Keep moving forward.</h1><p className="view-sub">Published calendar events and active notices from CampusOS.</p></div><button className="guest-disabled" disabled><LockKeyhole /> Personal tasks require sign-in</button></div>
    {error && <div className="inline-error"><AlertCircle />{error}</div>}
    <div className="planner-layout"><section className="planner-card"><div className="planner-month"><button onClick={() => setCursor(new Date(year, month - 1, 1))}><ChevronLeft /></button><h3>{cursor.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })}</h3><button onClick={() => setCursor(new Date(year, month + 1, 1))}><ChevronRight /></button></div><div className="week-days">{['M','T','W','T','F','S','S'].map((day,index)=><span key={`${day}-${index}`}>{day}</span>)}</div><div className="calendar-grid">{days.map((day,index) => day === null ? <span key={`blank-${index}`} /> : <button key={day} className={`${today.getFullYear() === year && today.getMonth() === month && today.getDate() === day ? 'today' : ''} ${eventDays.has(day) ? 'has-event' : ''}`}>{day}</button>)}</div></section>
      <section className="deadline-card"><p className="section-kicker">UP NEXT</p><h3>Deadlines & events</h3>{loading && <p className="loading-copy">Loading events…</p>}{!loading && events.filter(event => event.status !== 'EXPIRED').length === 0 && <div className="empty-state compact"><CalendarDays /><p>No upcoming published events.</p></div>}{events.filter(event => event.status !== 'EXPIRED').slice(0, 6).map(event => <div className="deadline" key={event.id}><time>{new Date(event.start_datetime).toLocaleDateString(undefined,{month:'short',day:'numeric'})}</time><div><strong>{event.title}</strong><span>{event.category} · {event.countdown_label}</span></div></div>)}</section></div>
    {!!notices.length && <section className="live-notices"><p className="section-kicker">ACTIVE NOTIFICATIONS</p>{notices.slice(0, 5).map(notice => <article key={notice.state_id}><CalendarDays /><div><strong>{notice.title}</strong><p>{notice.content}</p><small>{notice.source_doc}</small></div></article>)}</section>}
  </div>
}
