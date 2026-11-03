'use client'

import { useMemo, useState } from 'react'
import { Check, Compass, Search as SearchIcon, X } from 'lucide-react'
import { discoveries, searchResults, type SearchResult } from '@/lib/mock-data'
import { MIN_RELEVANCE, matchTopics, scoreDocument } from '@/lib/community-search'

type Indexed = SearchResult & { source: 'official' | 'discover' }

// Official documents first, then clubs, events and opportunities from Discover.
const index: Indexed[] = [
  ...searchResults.map((r) => ({ ...r, source: 'official' as const })),
  ...discoveries.map((d) => ({
    id: d.id,
    title: d.title,
    kind: d.clubType ? `${d.type} · ${d.clubType}` : d.type,
    excerpt: `${d.meta}. ${d.why}.`,
    icon: d.icon,
    source: 'discover' as const,
  })),
]

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const searching = query.trim().length > 0
  const topics = useMemo(() => (searching ? matchTopics(query) : []), [query, searching])
  const results = useMemo(
    () =>
      searching
        ? index
            .map((r) => ({ r, score: scoreDocument({ title: r.title, body: r.excerpt, extra: r.kind }, query, topics) }))
            .filter((x) => x.score >= MIN_RELEVANCE)
            .sort((a, b) => b.score - a.score)
            .map((x) => x.r)
        : index.filter((r) => r.source === 'official'),
    [query, searching, topics],
  )

  return (
    <div className="search-view">
      <div className="view-header">
        <div>
          <p className="section-kicker">CAMPUS KNOWLEDGE</p>
          <h1>Search everything.</h1>
          <p className="view-sub">Find verified answers across MIT Manipal.</p>
        </div>
      </div>
      <div className="large-search">
        <SearchIcon />
        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Try 'bunk limit', 'when are endsems' or 'robotics club'"
          aria-label="Search campus knowledge"
        />
        {searching && (
          <button className="icon-action" onClick={() => setQuery('')} aria-label="Clear search" title="Clear">
            <X size={14} />
          </button>
        )}
      </div>
      <div className="search-meta">
        <span>
          {results.length} result{results.length === 1 ? '' : 's'}
          {searching && topics.length > 0 ? ` · related to ${topics.slice(0, 3).join(', ')}` : ' · Verified sources'}
        </span>
      </div>
      <div className="result-list">
        {results.map((r) => (
          <article className="result-item" key={r.id}>
            <span className="result-icon">
              <r.icon />
            </span>
            <div>
              <span className="result-kind">{r.kind}</span>
              <h3>{r.title}</h3>
              <p>{r.excerpt}</p>
              <small>
                {r.source === 'official' ? (
                  <>
                    <Check /> Verified source · Updated recently
                  </>
                ) : (
                  <>
                    <Compass /> From Discover
                  </>
                )}
              </small>
            </div>
          </article>
        ))}
        {results.length === 0 && (
          <p className="view-sub">No results for &quot;{query.trim()}&quot;. Try different words, or ask MITra in chat.</p>
        )}
      </div>
    </div>
  )
}
