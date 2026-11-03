'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Heart, Lightbulb, MessageSquare, UserCheck, UserPlus, UserX } from 'lucide-react'
import { buildNotifications, READ_KEY, type AppNotification, type NotificationKind } from '@/lib/notifications'
import { communityQuestions, defaultProfile, type CommunityQuestion, type Profile } from '@/lib/mock-data'
import { useLocalState } from '@/lib/use-local-state'
import { useNetworkPeople } from '@/lib/use-network'

type Filter = 'all' | NotificationKind

const filters: { label: string; value: Filter }[] = [
  { label: 'All', value: 'all' },
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
}

export default function NotificationsPage() {
  const { people, activity, accept, ignore } = useNetworkPeople()
  const [profile] = useLocalState<Profile>('mitra_profile', defaultProfile)
  const [questions] = useLocalState<CommunityQuestion[]>('mitra_community', communityQuestions)
  const [myVotes] = useLocalState<Record<string, 1 | -1>>('mitra_community_votes', {})
  const [read, setRead] = useLocalState<string[]>(READ_KEY, [])
  const [filter, setFilter] = useState<Filter>('all')

  const all = buildNotifications({ people, activity, questions, myVotes, me: profile.name })
  const readSet = new Set(read)
  const unread = all.filter((n) => !readSet.has(n.id))
  const visible = filter === 'all' ? all : all.filter((n) => n.kind === filter)

  function markRead(id: string) {
    setRead((prev) => (prev.includes(id) ? prev : [...prev, id]))
  }

  function markAllRead() {
    setRead((prev) => [...new Set([...prev, ...all.map((n) => n.id)])])
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
          const count = f.value === 'all' ? unread.length : unread.filter((n) => n.kind === f.value).length
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
