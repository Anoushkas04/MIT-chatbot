'use client'

import { useMemo, useState } from 'react'
import { Check, ChevronRight, Filter, Search as SearchIcon } from 'lucide-react'
import { searchResults } from '@/lib/mock-data'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const results = useMemo(
    () =>
      query
        ? searchResults.filter((r) => `${r.title} ${r.excerpt}`.toLowerCase().includes(query.toLowerCase()))
        : searchResults,
    [query],
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
          placeholder="Try 'attendance rules' or 'clubs for designers'"
        />
        <button>
          <Filter /> Filters
        </button>
      </div>
      <div className="search-meta">
        <span>{results.length} results · Verified sources</span>
        <button>
          Most relevant <ChevronRight />
        </button>
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
                <Check /> Verified source · Updated recently
              </small>
            </div>
          </article>
        ))}
        {results.length === 0 && <p className="view-sub">No results for &quot;{query}&quot;.</p>}
      </div>
    </div>
  )
}
