'use client'

import { useCallback, useEffect, useState } from 'react'
import { Ban, CheckCircle2, UserX, XCircle } from 'lucide-react'
import { safetyApi, type AdminAppeal, type AdminPlea } from '@/lib/api'
import { useAdminError } from '@/lib/use-admin-error'

function PleaCard({ plea, decided, act }: { plea: AdminPlea; decided: boolean; act: (fn: () => Promise<unknown>) => Promise<void> }) {
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const s = plea.suspension
  const ends = s.ends_at ? new Date(s.ends_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : 'until lifted'

  async function decide(accept: boolean) {
    setBusy(true)
    await act(() => safetyApi.decidePlea(plea.id, accept, note.trim()))
    setBusy(false)
  }

  return (
    <article className="utility-card admin-post">
      <div className="community-meta">
        <strong>{plea.name}</strong>
        <time>sent {plea.time}</time>
        {decided && (
          <span className={`tag-chip plea-${plea.status}`}>
            {plea.status}
            {plea.decided_by ? ` · ${plea.decided_by}` : ''}
          </span>
        )}
      </div>
      <div className="admin-post-stats">
        <span className="admin-suspended-note">
          <Ban /> {s.source === 'auto_reports' ? 'Auto-suspended' : s.source === 'auto_strikes' ? 'Auto-suspended (strikes)' : `Suspended by ${s.by}`} · {ends}
          {s.status && s.status !== 'active' ? ` · now ${s.status}` : ''}
        </span>
      </div>
      <p className="admin-post-body">
        <b>Suspension reason:</b> {s.reason}
      </p>
      {plea.report_reasons.length > 0 && (
        <div className="tag-row">
          {plea.report_reasons.map(([r, n]) => (
            <span key={r} className="tag-chip">
              {r} × {n}
            </span>
          ))}
        </div>
      )}
      <blockquote className="plea-text">{plea.text}</blockquote>
      {decided ? (
        plea.decision_note && <p className="report-privacy">Note sent: {plea.decision_note}</p>
      ) : (
        <>
          <input className="plea-note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Optional note to the student" maxLength={500} />
          <div className="admin-actions">
            <button className="network-action connected" disabled={busy} onClick={() => decide(true)}>
              <CheckCircle2 /> Accept & lift suspension
            </button>
            <button className="network-action ghost" disabled={busy} onClick={() => decide(false)}>
              <XCircle /> Reject (keep suspension)
            </button>
          </div>
        </>
      )}
    </article>
  )
}

function AppealCard({ appeal, decided, act }: { appeal: AdminAppeal; decided: boolean; act: (fn: () => Promise<unknown>) => Promise<void> }) {
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)

  async function decide(accept: boolean) {
    setBusy(true)
    await act(() => safetyApi.decideAppeal(appeal.id, accept, note.trim()))
    setBusy(false)
  }

  return (
    <article className="utility-card admin-post">
      <div className="community-meta">
        <strong>{appeal.name}</strong>
        <span className="tag-chip">{appeal.email}</span>
        <time>sent {appeal.time}</time>
        {decided && (
          <span className={`tag-chip plea-${appeal.status}`}>
            {appeal.status}
            {appeal.decided_by ? ` · ${appeal.decided_by}` : ''}
          </span>
        )}
      </div>
      <div className="admin-post-stats">
        <span className="admin-suspended-note">
          <UserX /> Account {appeal.account_status === 'active' ? 'active again' : 'disabled'}
          {appeal.disabled_by ? ` · disabled by ${appeal.disabled_by} ${appeal.disabled_when}` : ''}
        </span>
      </div>
      <blockquote className="plea-text">{appeal.text}</blockquote>
      {decided ? (
        appeal.decision_note && <p className="report-privacy">Note: {appeal.decision_note}</p>
      ) : (
        <>
          <input className="plea-note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Optional note to the student" maxLength={500} />
          <div className="admin-actions">
            <button className="network-action connected" disabled={busy} onClick={() => decide(true)}>
              <CheckCircle2 /> Accept & re-enable account
            </button>
            <button className="network-action ghost" disabled={busy} onClick={() => decide(false)}>
              <XCircle /> Reject (keep disabled)
            </button>
          </div>
        </>
      )}
    </article>
  )
}

export default function AdminPleasPage() {
  const [tab, setTab] = useState<'pending' | 'decided'>('pending')
  const [pleas, setPleas] = useState<AdminPlea[]>([])
  const [appeals, setAppeals] = useState<AdminAppeal[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const handleError = useAdminError(setError)

  const load = useCallback(async () => {
    try {
      const [p, a] = await Promise.all([safetyApi.pleas(tab), safetyApi.appeals(tab)])
      setPleas(p.pleas)
      setAppeals(a.appeals)
      setError(null)
    } catch (e) {
      handleError(e)
    } finally {
      setLoading(false)
    }
  }, [tab, handleError])

  useEffect(() => {
    setLoading(true)
    load()
  }, [load])

  async function act(fn: () => Promise<unknown>) {
    try {
      await fn()
    } catch (e) {
      handleError(e)
    }
    await load()
  }

  return (
    <div className="view admin-view">
      <div className="view-header">
        <div>
          <p className="section-kicker">ADMIN · PLEAS</p>
          <h1>Pleas and appeals.</h1>
          <p className="view-sub">
            Suspended students send one plea per suspension from inside the app. Disabled students can&apos;t sign in, so they appeal from the
            sign-in page after confirming their learner email.
          </p>
        </div>
      </div>
      <div className="discover-tabs">
        <button className={tab === 'pending' ? 'active' : ''} onClick={() => setTab('pending')}>
          Waiting
        </button>
        <button className={tab === 'decided' ? 'active' : ''} onClick={() => setTab('decided')}>
          Decided
        </button>
      </div>
      {error && <p className="community-error">{error}</p>}
      <div className="admin-post-list">
        {loading && <p className="view-sub">Loading…</p>}
        {!loading && (
          <>
            <h3 className="insights-heading first">Suspension pleas</h3>
            {pleas.map((p) => (
              <PleaCard key={p.id} plea={p} decided={tab === 'decided'} act={act} />
            ))}
            {!error && pleas.length === 0 && <p className="view-sub">{tab === 'pending' ? 'No pleas waiting.' : 'No decided pleas yet.'}</p>}
            <h3 className="insights-heading">Disabled-account appeals</h3>
            {appeals.map((a) => (
              <AppealCard key={a.id} appeal={a} decided={tab === 'decided'} act={act} />
            ))}
            {!error && appeals.length === 0 && <p className="view-sub">{tab === 'pending' ? 'No appeals waiting.' : 'No decided appeals yet.'}</p>}
          </>
        )}
      </div>
    </div>
  )
}
