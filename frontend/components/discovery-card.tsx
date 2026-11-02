'use client'

import { Check, Heart } from 'lucide-react'
import { Sparkles } from 'lucide-react'
import type { DiscoveryItem } from '@/lib/mock-data'

export function DiscoveryCard({
  item,
  saved,
  onToggleSave,
}: {
  item: DiscoveryItem
  saved: boolean
  onToggleSave: () => void
}) {
  const Icon = item.icon
  return (
    <article className={`discovery-card ${item.tone}`}>
      <div className="discovery-top">
        <span className="discovery-icon">
          <Icon />
        </span>
        <button
          className={`save-button ${saved ? 'saved' : ''}`}
          onClick={onToggleSave}
          aria-label={saved ? `Remove ${item.title} from saved` : `Save ${item.title}`}
        >
          {saved ? <Check /> : <Heart />}
        </button>
      </div>
      <span className="pill">{item.type}</span>
      <h3>{item.title}</h3>
      <p>{item.meta}</p>
      <div className="why">
        <Sparkles /> {item.why}
      </div>
    </article>
  )
}
