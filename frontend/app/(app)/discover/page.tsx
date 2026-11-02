'use client'

import { Suspense, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { ArrowUpRight, Check, Filter, Heart } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { discoveries, type DiscoveryCategory } from '@/lib/mock-data'
import { useLocalState } from '@/lib/use-local-state'

const tabs: { label: string; value: DiscoveryCategory | 'all' }[] = [
  { label: 'For you', value: 'all' },
  { label: 'Clubs', value: 'club' },
  { label: 'Projects', value: 'project' },
  { label: 'Events', value: 'event' },
  { label: 'Opportunities', value: 'opportunity' },
]

function DiscoverInner() {
  const params = useSearchParams()
  const initialTab = (params.get('tab') as DiscoveryCategory | null) ?? 'all'
  const [tab, setTab] = useState<DiscoveryCategory | 'all'>(initialTab)
  const [saved, setSaved] = useLocalState<string[]>('mitra_saved', [])

  const list = tab === 'all' ? discoveries : discoveries.filter((d) => d.category === tab)

  function toggleSave(id: string) {
    setSaved((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  return (
    <div className="view">
      <div className="view-header">
        <div>
          <p className="section-kicker">DISCOVER</p>
          <h1>Find your next thing.</h1>
          <p className="view-sub">Clubs, projects, events and opportunities selected for you.</p>
        </div>
        <Button variant="outline">
          <Filter data-icon="inline-start" /> Filter
        </Button>
      </div>
      <div className="discover-tabs">
        {tabs.map((t) => (
          <button key={t.value} className={tab === t.value ? 'active' : ''} onClick={() => setTab(t.value)}>
            {t.label}
          </button>
        ))}
      </div>
      <div className="discover-list">
        {list.map((item) => {
          const Icon = item.icon
          const isSaved = saved.includes(item.id)
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
              <button
                className={`save-button ${isSaved ? 'saved' : ''}`}
                onClick={() => toggleSave(item.id)}
                aria-label={isSaved ? `Remove ${item.title} from saved` : `Save ${item.title}`}
              >
                {isSaved ? <Check /> : <Heart />}
              </button>
              <ArrowUpRight />
            </article>
          )
        })}
        {list.length === 0 && <p className="view-sub">Nothing here yet — check back soon.</p>}
      </div>
    </div>
  )
}

export default function DiscoverPage() {
  return (
    <Suspense fallback={null}>
      <DiscoverInner />
    </Suspense>
  )
}
