'use client'

import Link from 'next/link'
import { ArrowUpRight, Check } from 'lucide-react'
import { discoveries } from '@/lib/mock-data'
import { useLocalState } from '@/lib/use-local-state'

export default function SavedPage() {
  // Same key the heart buttons on Home and Discover write to.
  const [saved, setSaved] = useLocalState<string[]>('mitra_saved', [])
  // Keep the order things were saved in, newest first.
  const items = [...saved]
    .reverse()
    .map((id) => discoveries.find((d) => d.id === id))
    .filter((d) => d !== undefined)

  function unsave(id: string) {
    setSaved((prev) => prev.filter((x) => x !== id))
  }

  return (
    <div className="view">
      <div className="view-header">
        <div>
          <p className="section-kicker">SAVED</p>
          <h1>Saved for later.</h1>
          <p className="view-sub">Clubs, projects, events and opportunities you&apos;ve saved.</p>
        </div>
      </div>
      <div className="discover-list saved-list">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <article className={`discover-row ${item.tone}`} key={item.id}>
              <span className="discovery-icon">
                <Icon />
              </span>
              <div className="discover-info">
                <span className="pill">{item.type}</span>
                <h3>{item.title}</h3>
                <p>{item.meta}</p>
                <div className="why">{item.why}</div>
              </div>
              <button className="save-button saved" onClick={() => unsave(item.id)} aria-label={`Remove ${item.title} from saved`} title="Remove from saved">
                <Check />
              </button>
              <ArrowUpRight />
            </article>
          )
        })}
        {items.length === 0 && (
          <p className="view-sub">
            Nothing saved yet. Tap the heart on anything in <Link href="/discover" className="inline-link">Discover</Link> to keep it here.
          </p>
        )}
      </div>
    </div>
  )
}
