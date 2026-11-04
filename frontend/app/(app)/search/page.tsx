'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { BadgeCheck, Check, Compass, Download, FileText, MessageSquare, Search as SearchIcon, X } from 'lucide-react'
import type { CommunityQuestion } from '@/lib/mock-data'
import { discoveries, type DiscoveryItem } from '@/lib/discover-data'
import { MIN_RELEVANCE, matchTopics, scoreDocument, scoreQuestion } from '@/lib/community-search'
import { communityApi, libraryApi, type LibraryDocument, type LibraryHit } from '@/lib/api'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [debounced, setDebounced] = useState('')
  const [docHits, setDocHits] = useState<LibraryHit[]>([])
  const [docsState, setDocsState] = useState<'idle' | 'loading' | 'ready' | 'not-indexed' | 'error'>('idle')
  const [questions, setQuestions] = useState<CommunityQuestion[]>([])
  const [recentDocs, setRecentDocs] = useState<LibraryDocument[]>([])
  const [downloadError, setDownloadError] = useState<string | null>(null)

  const searching = query.trim().length > 0
  const topics = useMemo(() => (searching ? matchTopics(query) : []), [query, searching])

  // Community questions and the document list load once; document search follows the query.
  useEffect(() => {
    communityApi
      .list()
      .then((f) => setQuestions(f.questions))
      .catch(() => {})
    libraryApi
      .documents()
      .then((d) => setRecentDocs(d.documents.slice(0, 8)))
      .catch(() => {})
  }, [])

  useEffect(() => {
    const t = setTimeout(() => setDebounced(query.trim()), 300)
    return () => clearTimeout(t)
  }, [query])

  useEffect(() => {
    if (debounced.length < 2) {
      setDocHits([])
      setDocsState('idle')
      return
    }
    let cancelled = false
    setDocsState('loading')
    libraryApi
      .search(debounced)
      .then((res) => {
        if (cancelled) return
        setDocHits(res.results)
        setDocsState(res.indexed ? 'ready' : 'not-indexed')
      })
      .catch(() => !cancelled && setDocsState('error'))
    return () => {
      cancelled = true
    }
  }, [debounced])

  const communityHits = useMemo(
    () =>
      searching
        ? questions
            .map((q) => ({ q, score: scoreQuestion(q, query, topics) + (q.verified ? 1 : 0) }))
            .filter((x) => x.score >= MIN_RELEVANCE)
            .sort((a, b) => b.score - a.score)
            .slice(0, 5)
            .map((x) => x.q)
        : [],
    [questions, query, searching, topics],
  )

  const discoverHits = useMemo<DiscoveryItem[]>(
    () =>
      searching
        ? discoveries
            .map((d) => ({ d, score: scoreDocument({ title: d.title, body: `${d.meta}. ${d.why}. ${d.details ?? ''}`, extra: d.clubType ? `${d.type} ${d.clubType}` : d.type }, query, topics) }))
            .filter((x) => x.score >= MIN_RELEVANCE)
            .sort((a, b) => b.score - a.score)
            .slice(0, 5)
            .map((x) => x.d)
        : [],
    [query, searching, topics],
  )

  const total = docHits.length + communityHits.length + discoverHits.length

  async function download(name: string) {
    setDownloadError(null)
    try {
      await libraryApi.download(name)
    } catch (e) {
      setDownloadError(e instanceof Error ? e.message : 'Download failed.')
    }
  }

  return (
    <div className="search-view">
      <div className="view-header">
        <div>
          <p className="section-kicker">CAMPUS KNOWLEDGE</p>
          <h1>Search everything.</h1>
          <p className="view-sub">Official MIT Manipal documents, Community answers, clubs and events.</p>
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
          {searching
            ? `${total} result${total === 1 ? '' : 's'}${topics.length > 0 ? ` · related to ${topics.slice(0, 3).join(', ')}` : ''}${docsState === 'loading' ? ' · searching documents…' : ''}`
            : 'Official documents'}
        </span>
      </div>
      {downloadError && <p className="community-error">{downloadError}</p>}
      {searching && docsState === 'not-indexed' && (
        <p className="view-sub">Official documents are still being indexed. Community and Discover results are shown below.</p>
      )}
      {searching && docsState === 'error' && <p className="view-sub">Couldn&apos;t search the official documents right now.</p>}

      <div className="result-list">
        {!searching &&
          recentDocs.map((d) => (
            <article className="result-item" key={d.name}>
              <span className="result-icon">
                <FileText />
              </span>
              <div>
                <span className="result-kind">Official document · {d.type}</span>
                <h3>{d.title}</h3>
                <small>
                  <Check /> {d.size} · updated {d.updated}
                </small>
              </div>
              <button className="icon-action" onClick={() => download(d.name)} aria-label={`Download ${d.title}`} title="Download">
                <Download size={15} />
              </button>
            </article>
          ))}
        {!searching && recentDocs.length > 0 && (
          <Link href="/utilities" className="utility-link">
            All documents are in Utilities → Documents
          </Link>
        )}

        {docHits.map((h) => (
          <article className="result-item" key={h.source}>
            <span className="result-icon">
              <FileText />
            </span>
            <div>
              <span className="result-kind">Official document · {h.type}</span>
              <h3>{h.title}</h3>
              <p>{h.snippet}…</p>
              <small>
                <Check /> Verified source
              </small>
            </div>
            {h.downloadable && (
              <button className="icon-action" onClick={() => download(h.source)} aria-label={`Download ${h.title}`} title="Download">
                <Download size={15} />
              </button>
            )}
          </article>
        ))}

        {communityHits.map((q) => (
          <Link href="/community" className="result-item" key={q.id}>
            <span className="result-icon">
              <MessageSquare />
            </span>
            <div>
              <span className="result-kind">Community question{q.tags.length ? ` · ${q.tags.join(', ')}` : ''}</span>
              <h3>{q.title}</h3>
              <p>{q.body}</p>
              <small>
                {q.verified ? (
                  <>
                    <BadgeCheck /> Verified by the MITra team
                  </>
                ) : (
                  <>
                    {q.answers.length} answer{q.answers.length === 1 ? '' : 's'} from students
                  </>
                )}
              </small>
            </div>
          </Link>
        ))}

        {discoverHits.map((d) => (
          <article className="result-item" key={d.id}>
            <span className="result-icon">
              <d.icon />
            </span>
            <div>
              <span className="result-kind">{d.clubType ? `${d.clubType} club` : d.type}</span>
              <h3>{d.title}</h3>
              <p>
                {d.meta}. {d.why}.
              </p>
              <small>
                <Compass /> From Discover
              </small>
            </div>
          </article>
        ))}

        {searching && total === 0 && docsState !== 'loading' && (
          <p className="view-sub">No results for &quot;{query.trim()}&quot;. Try different words, or ask MITra in chat.</p>
        )}
      </div>
    </div>
  )
}
