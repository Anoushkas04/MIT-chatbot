'use client'

import { useEffect, useState } from 'react'
import { AlertCircle, CalendarDays, Heart, MessageCircle, Sparkles } from 'lucide-react'
import { getCommunityPosts, getTimeline, type CommunityPost, type TimelineEvent } from '@/lib/api'

export function DiscoverView() {
  const [tab, setTab] = useState<'events' | 'community'>('events')
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [posts, setPosts] = useState<CommunityPost[]>([])
  const [saved, setSaved] = useState<string[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  useEffect(() => { Promise.all([getTimeline(), getCommunityPosts('Clubs')]).then(([timeline, community]) => { setEvents(timeline.events.filter(event => event.status !== 'EXPIRED')); setPosts(community) }).catch(reason => setError(reason instanceof Error ? reason.message : 'Discover data failed to load.')).finally(() => setLoading(false)) }, [])
  const toggleSaved = (key: string) => setSaved(current => current.includes(key) ? current.filter(item => item !== key) : [...current, key])
  return <div className="view"><div className="view-header"><div><p className="section-kicker">DISCOVER · LIVE SOURCES</p><h1>Find your next thing.</h1><p className="view-sub">Published events and current club discussions—without inferred guest personalization.</p></div></div><div className="discover-tabs"><button className={tab === 'events' ? 'active' : ''} onClick={() => setTab('events')}>Events</button><button className={tab === 'community' ? 'active' : ''} onClick={() => setTab('community')}>Club discussions</button></div>{error && <div className="inline-error"><AlertCircle />{error}</div>}{loading && <p className="loading-copy">Loading discovery sources…</p>}
    {!loading && tab === 'events' && events.length === 0 && <div className="empty-state"><CalendarDays /><h3>No upcoming events</h3><p>New published calendar events will appear here.</p></div>}
    <div className="discover-list">{tab === 'events' ? events.map(event => <article className="discover-row blue" key={`event-${event.id}`}><span className="discovery-icon">{event.icon}</span><div className="discover-info"><span className="pill">{event.category}</span><h3>{event.title}</h3><p>{event.formatted_date} · {event.source}</p><div className="why"><Sparkles /> {event.countdown_label}</div></div><button className={`save-button ${saved.includes(`event-${event.id}`) ? 'saved' : ''}`} onClick={() => toggleSaved(`event-${event.id}`)}><Heart /></button></article>) : posts.map(post => <article className="discover-row yellow" key={`post-${post.id}`}><span className="discovery-icon"><MessageCircle /></span><div className="discover-info"><span className="pill">{post.sub_community}</span><h3>{post.title}</h3><p>{post.content}</p><div className="why"><MessageCircle /> {post.comments.length} replies · {post.upvotes} upvotes</div></div></article>)}</div>
  </div>
}
