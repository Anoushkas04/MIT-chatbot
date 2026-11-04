'use client'

import { Suspense, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Check, ChevronDown, Download, ExternalLink, Heart, Mail } from 'lucide-react'
import { discoveries, forYou, type DiscoveryCategory } from '@/lib/discover-data'
import type { ClubCategory } from '@/lib/clubs'
import { defaultProfile, type Profile } from '@/lib/mock-data'
import { libraryApi } from '@/lib/api'
import { useLocalState } from '@/lib/use-local-state'

const tabs: { label: string; value: DiscoveryCategory | 'all' }[] = [
  { label: 'For you', value: 'all' },
  { label: 'Clubs', value: 'club' },
  { label: 'Events', value: 'event' },
  { label: 'Opportunities', value: 'opportunity' },
]

const clubTypes: ClubCategory[] = ['Technical', 'Non-technical']

const emptyText: Record<DiscoveryCategory | 'all', string> = {
  all: 'Add interests to your profile to see clubs picked for you.',
  club: 'No clubs match this filter.',
  event: 'No official events are listed yet.',
  opportunity: 'No official opportunities are listed yet.',
}

function DiscoverInner() {
  const params = useSearchParams()
  const initialTab = (params.get('tab') as DiscoveryCategory | null) ?? 'all'
  const [tab, setTab] = useState<DiscoveryCategory | 'all'>(tabs.some((t) => t.value === initialTab) ? initialTab : 'all')
  const [clubType, setClubType] = useState<ClubCategory | 'all'>('all')
  const [open, setOpen] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useLocalState<string[]>('mitra_saved', [])
  const [profile] = useLocalState<Profile>('mitra_profile', defaultProfile)

  const inTab = tab === 'all' ? forYou(profile.interests) : discoveries.filter((d) => d.category === tab)
  const list = tab === 'club' && clubType !== 'all' ? inTab.filter((d) => d.clubType === clubType) : inTab

  function toggleSave(id: string) {
    setSaved((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  async function download(name: string) {
    setError(null)
    try {
      await libraryApi.download(name)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Download failed.')
    }
  }

  return (
    <div className="view">
      <div className="view-header">
        <div>
          <p className="section-kicker">DISCOVER</p>
          <h1>Find your next thing.</h1>
          <p className="view-sub">Official MIT clubs, campus fests and opportunities from MIT notices.</p>
        </div>
      </div>
      <div className="discover-tabs">
        {tabs.map((t) => (
          <button key={t.value} className={tab === t.value ? 'active' : ''} onClick={() => setTab(t.value)}>
            {t.label}
          </button>
        ))}
      </div>
      {tab === 'club' && (
        <div className="tag-picker club-filter" role="group" aria-label="Filter clubs by type">
          <button className={clubType === 'all' ? 'active' : ''} onClick={() => setClubType('all')}>
            All
          </button>
          {clubTypes.map((t) => (
            <button key={t} className={clubType === t ? 'active' : ''} onClick={() => setClubType(t)}>
              {t}
            </button>
          ))}
        </div>
      )}
      {error && <p className="community-error">{error}</p>}
      <div className="discover-list">
        {list.map((item) => {
          const Icon = item.icon
          const isSaved = saved.includes(item.id)
          const isOpen = open === item.id
          return (
            <article className={`discover-row expandable ${item.tone} ${item.status === 'past' ? 'past' : ''}`} key={item.id}>
              <div className="discover-main">
                <span className="discovery-icon">
                  <Icon />
                </span>
                <div className="discover-info">
                  <span className="pill">{item.clubType ? `${item.clubType} club` : item.type}</span>
                  {item.status === 'tentative' && <span className="pill status">Dates approximate</span>}
                  {item.status === 'past' && <span className="pill status">Past</span>}
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
                <button
                  className={`icon-ghost discover-toggle ${isOpen ? 'open' : ''}`}
                  onClick={() => setOpen(isOpen ? null : item.id)}
                  aria-expanded={isOpen}
                  aria-label={isOpen ? `Hide details for ${item.title}` : `Show details for ${item.title}`}
                >
                  <ChevronDown />
                </button>
              </div>
              {isOpen && (
                <div className="discover-details">
                  {item.details?.split('\n\n').map((p, i) => <p key={i}>{p}</p>)}
                  <div className="discover-links">
                    {item.emails?.map((e) => (
                      <a key={e} href={`mailto:${e}`}>
                        <Mail /> {e}
                      </a>
                    ))}
                    {item.url && (
                      <a href={item.url} target="_blank" rel="noreferrer">
                        <ExternalLink /> Official page
                      </a>
                    )}
                    {item.sourceDoc && (
                      <button onClick={() => download(item.sourceDoc!)}>
                        <Download /> Official notice
                      </button>
                    )}
                  </div>
                  <small>Source: {item.source}</small>
                </div>
              )}
            </article>
          )
        })}
        {list.length === 0 && <p className="view-sub">{emptyText[tab]}</p>}
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
