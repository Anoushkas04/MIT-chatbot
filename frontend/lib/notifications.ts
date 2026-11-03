import { matchTopics } from '@/lib/community-search'
import {
  communityQuestions,
  defaultActivity,
  defaultNetworkPeople,
  defaultProfile,
  type ActivityEvent,
  type CommunityComment,
  type CommunityQuestion,
  type NetworkPerson,
  type Profile,
} from '@/lib/mock-data'

/**
 * Notifications are derived from what's already stored locally (network requests,
 * the activity log, community threads and votes) rather than kept as a separate
 * feed, so they always reflect current state. Ids are stable per event, which is
 * what the read/unread list keys on.
 */
export type NotificationKind = 'request' | 'response' | 'like' | 'recommendation'

export type AppNotification = {
  id: string
  kind: NotificationKind
  title: string
  detail?: string
  time?: string
  href: string
  personId?: string // set for connection requests, which can be answered inline
}

export const READ_KEY = 'mitra_notifications_read'

type Votes = Record<string, 1 | -1>

function relativeTime(at?: number, fallback?: string): string | undefined {
  if (!at) return fallback
  const mins = Math.round((Date.now() - at) / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.round(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.round(hours / 24)}d ago`
}

function shorten(text: string, max = 70) {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

function questionTopics(q: CommunityQuestion): string[] {
  return q.tags.length > 0 ? q.tags : matchTopics(`${q.title} ${q.body}`).slice(0, 2)
}

export function buildNotifications({
  people,
  activity,
  questions,
  myVotes,
  me,
}: {
  people: NetworkPerson[]
  activity: ActivityEvent[]
  questions: CommunityQuestion[]
  myVotes: Votes
  me: string
}): AppNotification[] {
  const out: AppNotification[] = []
  const byId = new Map(people.map((p) => [p.id, p]))

  // Requests: people waiting on you.
  for (const p of people.filter((x) => x.status === 'incoming')) {
    out.push({
      id: `req-${p.id}`,
      kind: 'request',
      title: `${p.name} wants to connect`,
      detail: [p.branch, p.semester].filter(Boolean).join(' · '),
      href: '/network',
      personId: p.id,
    })
  }

  // Responses: accepted requests from the activity log, newest first.
  for (const e of [...activity].sort((a, b) => (b.at ?? 0) - (a.at ?? 0))) {
    const p = byId.get(e.personId)
    if (!p || p.status === 'blocked') continue
    out.push({
      id: e.id,
      kind: 'response',
      title: `${p.name} accepted your connection request`,
      detail: 'You can message them now.',
      time: relativeTime(e.at, e.time),
      href: '/network',
    })
  }

  // Responses and likes on your own community posts.
  const likes: AppNotification[] = []
  function walk(nodes: CommunityComment[], q: CommunityQuestion) {
    for (const c of nodes) {
      if (c.deleted) continue
      const mine = c.author === me
      for (const r of c.replies ?? []) {
        if (mine && r.author !== me && !r.deleted) {
          out.push({
            id: `reply-${r.id}`,
            kind: 'response',
            title: `${r.author} replied to your answer`,
            detail: shorten(r.body),
            time: r.time,
            href: '/community',
          })
        }
      }
      const others = c.votes - (myVotes[c.id] ?? 0)
      if (mine && others > 0) {
        likes.push({
          id: `like-${c.id}-${others}`,
          kind: 'like',
          title: `Your answer on "${shorten(q.title, 50)}" got ${others} upvote${others === 1 ? '' : 's'}`,
          detail: shorten(c.body),
          href: '/community',
        })
      }
      walk(c.replies ?? [], q)
    }
  }
  for (const q of questions) {
    if (q.author === me) {
      for (const a of q.answers) {
        if (a.author !== me && !a.deleted) {
          out.push({
            id: `reply-${a.id}`,
            kind: 'response',
            title: `${a.author} answered your question`,
            detail: shorten(q.title),
            time: a.time,
            href: '/community',
          })
        }
      }
      const others = q.votes - (myVotes[q.id] ?? 0)
      if (others > 0) {
        likes.push({
          id: `like-${q.id}-${others}`,
          kind: 'like',
          title: `Your question got ${others} upvote${others === 1 ? '' : 's'}`,
          detail: shorten(q.title),
          href: '/community',
        })
      }
    }
    walk(q.answers, q)
  }
  out.push(...likes)

  // Recommendations: threads from the community's most-posted topics that you didn't write,
  // unanswered ones first (they need help), then by votes.
  const topicCounts = new Map<string, number>()
  for (const q of questions) for (const t of questionTopics(q)) topicCounts.set(t, (topicCounts.get(t) ?? 0) + 1)
  const topTopics = [...topicCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 2).map(([t]) => t)
  const recs = questions
    .filter((q) => q.author !== me && questionTopics(q).some((t) => topTopics.includes(t)))
    .sort((a, b) => (a.answers.length === 0 ? 0 : 1) - (b.answers.length === 0 ? 0 : 1) || b.votes - a.votes)
    .slice(0, 3)
  for (const q of recs) {
    const topic = questionTopics(q).find((t) => topTopics.includes(t))
    out.push({
      id: `rec-${q.id}`,
      kind: 'recommendation',
      title: shorten(q.title),
      detail: `Popular in ${topic} · ${q.answers.length === 0 ? 'No answers yet. Can you help?' : `${q.answers.length} answer${q.answers.length === 1 ? '' : 's'}`}`,
      time: q.time,
      href: '/community',
    })
  }

  return out
}

function readJSON<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

/** Unread count straight from storage, for places (like the sidebar) that don't hold the state. */
export function countUnreadNotifications(): number {
  const profile = readJSON<Profile>('mitra_profile', defaultProfile)
  const list = buildNotifications({
    people: readJSON('mitra_network', defaultNetworkPeople),
    activity: readJSON('mitra_activity', defaultActivity),
    questions: readJSON('mitra_community', communityQuestions),
    myVotes: readJSON('mitra_community_votes', {}),
    me: profile.name,
  })
  const read = new Set(readJSON<string[]>(READ_KEY, []))
  return list.filter((n) => !read.has(n.id)).length
}
