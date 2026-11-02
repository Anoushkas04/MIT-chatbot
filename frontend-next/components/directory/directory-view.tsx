'use client'

import { useEffect, useState } from 'react'
import { AlertCircle, Building2, ChevronLeft, ChevronRight, Mail, Search } from 'lucide-react'
import { getFaculty, type FacultyResponse } from '@/lib/api'

export function DirectoryView() {
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<FacultyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  useEffect(() => { const timer = window.setTimeout(() => { setLoading(true); setError(''); getFaculty(query, page).then(setData).catch(reason => setError(reason instanceof Error ? reason.message : 'Directory search failed.')).finally(() => setLoading(false)) }, 250); return () => window.clearTimeout(timer) }, [query, page])
  return <div className="view"><div className="view-header"><div><p className="section-kicker">SOURCE-BACKED DIRECTORY</p><h1>Faculty & cabins.</h1><p className="view-sub">Loaded from the repository’s faculty CSV files, not a hardcoded demo list.</p></div></div><div className="large-search"><Search /><input value={query} onChange={event => { setQuery(event.target.value); setPage(1) }} placeholder="Search name, department, cabin, email…" /></div><div className="search-meta"><span>{loading ? 'Searching directory…' : `${data?.count ?? 0} faculty records`}</span></div>{error && <div className="inline-error"><AlertCircle />{error}</div>}<div className="faculty-grid">{data?.data.map(member => <article key={member.id}><div className="faculty-avatar">{member.name.split(' ').filter(Boolean).slice(-2).map(word => word[0]).join('').toUpperCase()}</div><div><h3>{member.name}</h3><p>{member.designation} · {member.dept}</p>{member.cabin && <span><Building2 />{member.cabin}</span>}<a href={`mailto:${member.email}`}><Mail />{member.email}</a><small>Source: {member.source}</small></div></article>)}</div>{!loading && data?.data.length === 0 && <div className="empty-state"><Search /><h3>No matching faculty record</h3></div>}{(data?.total_pages ?? 0) > 1 && <div className="pagination"><button disabled={page === 1} onClick={() => setPage(value => value - 1)}><ChevronLeft />Previous</button><span>Page {page} of {data?.total_pages}</span><button disabled={page === data?.total_pages} onClick={() => setPage(value => value + 1)}>Next<ChevronRight /></button></div>}</div>
}
