'use client'

import { useEffect, useState } from 'react'
import { AlertCircle, ArrowUpRight, Check, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { resolveApiUrl, searchCampus, type SearchResponse } from '@/lib/api'

const categories = ['all', 'documents', 'events', 'faculty', 'community']

export function SearchView() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('all')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true); setError('')
      searchCampus(query, category, page).then(setData).catch(reason => setError(reason instanceof Error ? reason.message : 'Search failed.')).finally(() => setLoading(false))
    }, 250)
    return () => window.clearTimeout(timer)
  }, [query, category, page])

  return <div className="search-view"><div className="view-header"><div><p className="section-kicker">LIVE CAMPUS KNOWLEDGE</p><h1>Search everything.</h1><p className="view-sub">Documents, faculty directories, events, and community posts from the backend.</p></div></div>
    <div className="large-search"><Search /><input autoFocus value={query} onChange={event => { setQuery(event.target.value); setPage(1) }} placeholder="Try ‘attendance’, ‘faculty’, or ‘hackathon’" /></div>
    <div className="filter-row">{categories.map(item => <button key={item} className={category === item ? 'active' : ''} onClick={() => { setCategory(item); setPage(1) }}>{item}</button>)}</div>
    <div className="search-meta"><span>{loading ? 'Searching live sources…' : `${data?.total_results ?? 0} results`}</span><span>{data ? `${data.official_count} official · ${data.community_count} community` : ''}</span></div>
    {error && <div className="inline-error"><AlertCircle /> {error}</div>}
    {!loading && !error && data?.results.length === 0 && <div className="empty-state"><Search /><h3>No matching campus sources</h3><p>Try fewer words or another source filter.</p></div>}
    <div className="result-list">{data?.results.map(result => <a className="result-item" key={result.id} href={resolveApiUrl(result.link_target)} target="_blank" rel="noreferrer"><span className="result-icon"><Search /></span><div><span className="result-kind">{result.badge} · {result.category}</span><h3>{result.title}</h3><p>{result.snippet}</p><small><Check /> {result.source} · relevance {Math.round(result.relevance * 100)}%</small></div><ArrowUpRight /></a>)}</div>
    {(data?.total_pages ?? 0) > 1 && <div className="pagination"><button disabled={page === 1} onClick={() => setPage(value => value - 1)}><ChevronLeft /> Previous</button><span>Page {page} of {data?.total_pages}</span><button disabled={page === data?.total_pages} onClick={() => setPage(value => value + 1)}>Next <ChevronRight /></button></div>}
  </div>
}
