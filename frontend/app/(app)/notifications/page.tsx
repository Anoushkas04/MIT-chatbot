'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { BadgeCheck, Heart, Lightbulb, MessageSquare, UserCheck, UserPlus, UserX } from 'lucide-react'
import {
  buildNotifications,
  fromServer,
  NOTIFICATIONS_CHANGED,
  READ_KEY,
  SEEN_KEY,
  SERVER_KEY,
  type AppNotification,
  type NotificationKind,
} from '@/lib/notifications'
import { defaultProfile, type CommunityQuestion, type Profile } from '@/lib/mock-data'
import { communityApi, meApi, type ServerNotification } from '@/lib/api'
import { useLocalState } from '@/lib/use-local-state'
import { useNetworkPeople } from '@/lib/use-network'

type Filter = 'all' | NotificationKind

const filters: { label: string; value: Filter }[] = [
  { label: 'All', value: 'all' },
  { label: 'From MITra', value: 'official' },
  { label: 'Requests', value: 'request' },
  { label: 'Responses', value: 'response' },
  { label: 'Likes', value: 'like' },
  { label: 'Recommended', value: 'recommendation' },
]

const kindIcon: Record<NotificationKind, typeof Heart> = {
  request: UserPlus,
  response: MessageSquare,
  like: Heart,
  recommendation: Lightbulb,
  official: BadgeCheck,
}

export default function NotificationsPage() {
  const { people, activity, unread: unreadMessages, accept, ignore } = useNetworkPeople()
  const [profile] = useLocalState<Profile>('mitra_profile', defaultProfile)
  // Cached copy of the backend feed; refreshed below so replies and likes are current.
  const [questions, setQuestions] = useLocalState<CommunityQuestion[]>('mitra_community', [])
  const [myVotes, setMyVotes] = useLocalState<Record<string, 1 | -1>>('mitra_community_votes', {})
  const [read, setRead] = useLocalState<string[]>(READ_KEY, [])
  const [seen, setSeen] = useLocalState<string[]>(SEEN_KEY, [])
  const [server, setServer] = useLocalState<ServerNotification[]>(SERVER_KEY, [])
  const [filter, setFilter] = useState<Filter>('all')

  useEffect(() => {
    communityApi
      .list()
      .then((feed) => {
        setQuestions(feed.questions)
        setMyVotes(feed.myVotes)
      })
      .catch(() => {}) // offline: keep showing the cached feed
    meApi
      .notifications()
      .then((res) => setServer(res.notifications))
      .catch(() => {})
  }, [setQuestions, setMyVotes, setServer])

  const official = fromServer(server)
  const serverRead = new Set(official.filter((n) => n.serverRead).map((n) => n.id))
  // Newest MITra messages first, then the activity built from local and community data.
  const all: AppNotification[] = [...official, ...buildNotifications({ people, activity, questions, myVotes, me: profile.name, unreadMessages })]
  const readSet = new Set([...read, ...serverRead])
  const unread = all.filter((n) => !readSet.has(n.id))
  const seenSet = new Set([...readSet, ...seen])
  const unseen = all.filter((n) => !seenSet.has(n.id))
  const visible = filter === 'all' ? all : all.filter((n) => n.kind === filter)

  // Opening a section tab counts as seeing what's in it, which clears that tab's badge.
  // "All" doesn't, so the sidebar badge only goes once every section has been visited.
  const newlySeen = filter === 'all' ? [] : visible.filter((n) => !seenSet.has(n.id)).map((n) => n.id)
  const newlySeenKey = newlySeen.join('|')
  useEffect(() => {
    if (!newlySeenKey) return
    setSeen((prev) => [...new Set([...prev, ...newlySeenKey.split('|')])])
  }, [newlySeenKey, setSeen])

  // Runs after useLocalState has saved the lists, so the sidebar recounts from fresh storage
  useEffect(() => {
    window.dispatchEvent(new Event(NOTIFICATIONS_CHANGED))
  }, [read, seen])

  function markRead(id: string) {
    setRead((prev) => (prev.includes(id) ? prev : [...prev, id]))
    if (id.startsWith('srv-')) meApi.markRead(id).catch(() => {})
  }

  function markAllRead() {
    setRead((prev) => [...new Set([...prev, ...all.map((n) => n.id)])])
    if (official.some((n) => !n.serverRead)) meApi.markAllRead().catch(() => {})
  }

  function respond(n: AppNotification, accepted: boolean) {
    if (!n.personId) return
    if (accepted) accept(n.personId)
    else ignore(n.personId)
    markRead(n.id)
  }

  return (
    <div className="view">
      <div className="view-header">
        <div>
          <p className="section-kicker">NOTIFICATIONS</p>
          <h1>What&apos;s new.</h1>
          <p className="view-sub">Requests, responses, likes and threads picked for you from the community.</p>
        </div>
        {unread.length > 0 && (
          <button className="text-button" onClick={markAllRead}>
            Mark all as read
          </button>
        )}
      </div>

      <div className="discover-tabs">
        {filters.map((f) => {
          const count = f.value === 'all' ? unseen.length : unseen.filter((n) => n.kind === f.value).length
          return (
            <button key={f.value} className={filter === f.value ? 'active' : ''} onClick={() => setFilter(f.value)}>
              {f.label} {count > 0 && <span className="nav-badge inline">{count}</span>}
            </button>
          )
        })}
      </div>

      <div className="notification-list">
        {visible.map((n) => {
          const Icon = kindIcon[n.kind]
          const isUnread = !readSet.has(n.id)
          return (
            <article key={n.id} className={`notification-row ${isUnread ? 'unread' : ''}`}>
              <span className={`notification-icon ${n.kind}`}>
                <Icon />
              </span>
              <Link href={n.href} className="notification-body" onClick={() => markRead(n.id)}>
                <strong>{n.title}</strong>
                {n.detail && <span>{n.detail}</span>}
                {n.time && <time>{n.time}</time>}
              </Link>
              {n.kind === 'request' && (
                <div className="network-action-row">
                  <button className="network-action" onClick={() => respond(n, true)}>
                    <UserCheck /> Accept
                  </button>
                  <button className="network-action ghost" onClick={() => respond(n, false)} aria-label="Decline request">
                    <UserX />
                  </button>
                </div>
              )}
              {isUnread && n.kind !== 'request' && <i className="unread-dot" aria-label="Unread" />}
            </article>
          )
        })}
        {visible.length === 0 && <p className="view-sub">Nothing here yet.</p>}
      </div>
    </div>
  )
}
