'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowUpRight, Bell, Search, Send, Sparkles } from 'lucide-react'
import { DiscoveryCard } from '@/components/discovery-card'
import { NetworkPersonCard } from '@/components/network-person-card'
import { useLocalState } from '@/lib/use-local-state'
import { useNetworkPeople } from '@/lib/use-network'
import { defaultPlannerTasks, defaultProfile, discoveries, type PlannerTask, type Profile } from '@/lib/mock-data'

export default function HomePage() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [profile] = useLocalState<Profile>('mitra_profile', defaultProfile)
  const [saved, setSaved] = useLocalState<string[]>('mitra_saved', [])
  const [tasks] = useLocalState<PlannerTask[]>('mitra_planner_tasks', defaultPlannerTasks)
  const { people, connect, dismiss } = useNetworkPeople()

  const todayLabel = new Date()
    .toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
    .toUpperCase()

  const upNext = tasks
    .filter((t) => !t.done)
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(0, 3)

  const suggestions = people.filter((p) => p.status === 'suggested').slice(0, 5)

  function toggleSave(id: string) {
    setSaved((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  function submitSearch(e: React.FormEvent) {
    e.preventDefault()
    const q = query.trim()
    router.push(q ? `/chat?q=${encodeURIComponent(q)}` : '/chat')
  }

  return (
    <div className="view">
      <div className="view-header">
        <div>
          <p className="section-kicker">{todayLabel}</p>
          <h1>
            Good morning, {profile.name.split(' ')[0]} <span>✦</span>
          </h1>
          <p className="view-sub">Here&apos;s what&apos;s happening around your campus.</p>
        </div>
        <div className="header-actions">
          <Link href="/notifications" className="icon-button" aria-label="Notifications">
            <Bell />
            <i />
          </Link>
          <div className="header-avatar" style={{ background: profile.avatar.color }}>
            {profile.avatar.emoji}
          </div>
        </div>
      </div>

      <form className="search-bar" onSubmit={submitSearch}>
        <Search />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search campus, courses, events, anything..."
          aria-label="Search MITra"
        />
        <button type="submit" aria-label="Ask MITra" className="search-submit">
          <Send />
        </button>
      </form>

      <div className="home-grid">
        <section className="ask-card">
          <div className="ask-glow" />
          <div className="ask-content">
            <div className="ai-avatar">
              <Sparkles />
            </div>
            <p className="section-kicker">YOUR AI CAMPUS COMPANION</p>
            <h2>What&apos;s on your mind?</h2>
            <p>Ask about academics, campus life, events, or just get pointed in the right direction.</p>
            <Link href="/chat" className="ask-input">
              <span>Ask MITra anything...</span>
              <Send />
            </Link>
            <div className="suggestions">
              <Link href="/chat?q=What can I do this weekend?">What can I do this weekend?</Link>
              <Link href="/chat?q=Explain attendance rules">Explain attendance rules</Link>
            </div>
          </div>
        </section>
        <section className="today-card">
          <div className="card-heading">
            <div>
              <p className="section-kicker">YOUR DAY</p>
              <h3>Today at a glance</h3>
            </div>
            <Link href="/planner">
              View planner <ArrowUpRight />
            </Link>
          </div>
          <div className="timeline">
            {upNext.length === 0 && <p className="view-sub">Nothing on your planner yet.</p>}
            {upNext.map((task, i) => (
              <div key={task.id}>
                <time>
                  {new Date(task.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </time>
                <span className={`timeline-line ${['blue-line', 'coral-line', 'yellow-line'][i % 3]}`} />
                <article>
                  <strong>{task.title}</strong>
                  <span>{task.category}</span>
                </article>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="section-row">
        <div>
          <p className="section-kicker">CURATED FOR YOU</p>
          <h2>Worth a look</h2>
        </div>
        <Link href="/discover" className="link-button">
          See all discoveries <ArrowUpRight />
        </Link>
      </div>
      <div className="discovery-grid">
        {discoveries.slice(0, 3).map((item) => (
          <DiscoveryCard key={item.id} item={item} saved={saved.includes(item.id)} onToggleSave={() => toggleSave(item.id)} />
        ))}
      </div>

      <div className="section-row">
        <div>
          <p className="section-kicker">SUGGESTED FOR YOU</p>
          <h2>Your network</h2>
        </div>
        <Link href="/network" className="link-button">
          See all <ArrowUpRight />
        </Link>
      </div>
      <div className="network-carousel">
        {suggestions.length === 0 && <p className="view-sub">You&apos;re all caught up on suggestions.</p>}
        {suggestions.map((person) => (
          <NetworkPersonCard key={person.id} person={person} onConnect={() => connect(person.id)} onDismiss={() => dismiss(person.id)} />
        ))}
      </div>
    </div>
  )
}
