'use client'

import { Suspense, useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { AlertTriangle, Ban, CheckCircle2, Lock, ShieldAlert, UserX, XCircle } from 'lucide-react'
import { safetyApi, type AdminAppeal, type AdminPlea, type AdminSuspension, type ReportGroup, type WarningTemplate } from '@/lib/api'
import { useAdminError } from '@/lib/use-admin-error'

type Templates = { warnings: WarningTemplate[]; days: number[]; threshold: number }

function sourceLabel(s: AdminSuspension) {
  if (s.source === 'auto_reports') return 'Automatic (reported by many students)'
  if (s.source === 'auto_strikes') return 'Automatic (guideline strikes)'
  return `By ${s.by}`
}

function endsLabel(endsAt: string | null) {
  return endsAt ? `until ${new Date(endsAt).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}` : 'until lifted'
}

function DecisionPanel({ group, templates, onDecided }: { group: ReportGroup; templates: Templates; onDecided: (fn: () => Promise<unknown>) => Promise<void> }) {
  const [mode, setMode] = useState<'none' | 'innocent' | 'warn' | 'suspend'>('none')
  const [warningKey, setWarningKey] = useState('')
  const [warningText, setWarningText] = useState('')
  const [days, setDays] = useState<number | null>(7)
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)

  async function run(fn: () => Promise<unknown>) {
    setBusy(true)
    await onDecided(fn)
    setBusy(false)
    setMode('none')
  }

  if (!group.has_account) {
    return (
      <div className="admin-actions">
        <span className="report-privacy">This person has no MITra account, so there&apos;s no one to warn or suspend.</span>
        <button className="network-action connected" disabled={busy} onClick={() => run(() => safetyApi.decide({ target: group.target, decision: 'innocent' }))}>
          <CheckCircle2 /> Dismiss reports
        </button>
      </div>
    )
  }

  return (
    <>
      <div className="admin-actions">
        <button className={`network-action connected ${mode === 'innocent' ? 'selected' : ''}`} onClick={() => setMode(mode === 'innocent' ? 'none' : 'innocent')}>
          <CheckCircle2 /> Innocent
        </button>
        <button className={`network-action ${mode === 'warn' ? 'selected' : ''}`} onClick={() => setMode(mode === 'warn' ? 'none' : 'warn')}>
          <AlertTriangle /> Send warning
        </button>
        <button className={`network-action ghost ${mode === 'suspend' ? 'selected' : ''}`} onClick={() => setMode(mode === 'suspend' ? 'none' : 'suspend')}>
          <Ban /> Suspend
        </button>
      </div>

      {mode === 'innocent' && (
        <div className="admin-composer">
          <p className="report-privacy">
            Dismisses all {group.reports.length} open report(s){group.suspension?.source === 'auto_reports' ? ' and lifts the automatic suspension' : ''}. {group.name} isn&apos;t notified;
            reporters are told their report was reviewed.
          </p>
          <div className="composer-actions">
            <button className="text-button" onClick={() => setMode('none')}>
              Cancel
            </button>
            <button className="community-ask-btn small" disabled={busy} onClick={() => run(() => safetyApi.decide({ target: group.target, decision: 'innocent' }))}>
              Mark innocent
            </button>
          </div>
        </div>
      )}

      {mode === 'warn' && (
        <div className="admin-composer">
          <select
            value={warningKey}
            onChange={(e) => {
              const t = templates.warnings.find((w) => w.key === e.target.value)
              setWarningKey(e.target.value)
              setWarningText(t?.text ?? '')
            }}
            aria-label="Warning template"
          >
            <option value="">Choose a warning…</option>
            {templates.warnings.map((w) => (
              <option key={w.key} value={w.key}>
                {w.label}
              </option>
            ))}
          </select>
          <textarea value={warningText} onChange={(e) => setWarningText(e.target.value)} placeholder="The warning the student will receive (you can edit the template)" />
          {group.suspension?.source === 'auto_reports' && !group.suspension.reviewed && (
            <p className="report-privacy">Sending a warning also lifts the pending automatic suspension.</p>
          )}
          <div className="composer-actions">
            <button className="text-button" onClick={() => setMode('none')}>
              Cancel
            </button>
            <button
              className="community-ask-btn small"
              disabled={busy || warningText.trim().length < 10}
              onClick={() =>
                run(() =>
                  safetyApi.decide({
                    target: group.target,
                    decision: 'warn',
                    // Only tag the template when it's sent as written, so the audit log is accurate.
                    warning_key: templates.warnings.find((w) => w.key === warningKey)?.text === warningText.trim() ? warningKey : undefined,
                    warning_text: warningText.trim(),
                  }),
                )
              }
            >
              Send warning
            </button>
          </div>
        </div>
      )}

      {mode === 'suspend' && (
        <div className="admin-delete-confirm">
          <p>Suspend {group.name}? They can still sign in and read, but can&apos;t post, reply, vote or report, and they can send one plea.</p>
          <div className="tag-picker">
            {templates.days.map((d) => (
              <button key={d} className={days === d ? 'active' : ''} onClick={() => setDays(d)}>
                {d} day{d === 1 ? '' : 's'}
              </button>
            ))}
            <button className={days === null ? 'active' : ''} onClick={() => setDays(null)}>
              Until lifted
            </button>
          </div>
          <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason shown to the student, e.g. Harassing classmates in private chats" maxLength={300} />
          <div className="composer-actions">
            <button className="text-button" onClick={() => setMode('none')} autoFocus>
              Cancel
            </button>
            <button
              className="community-ask-btn small danger"
              disabled={busy || !reason.trim()}
              onClick={() => run(() => safetyApi.decide({ target: group.target, decision: 'suspend', days, reason: reason.trim() }))}
            >
              Suspend {days ? `for ${days} day${days === 1 ? '' : 's'}` : 'until lifted'}
            </button>
          </div>
        </div>
      )}
    </>
  )
}

function GroupCard({ group, templates, closed, act }: { group: ReportGroup; templates: Templates; closed: boolean; act: (fn: () => Promise<unknown>) => Promise<void> }) {
  return (
    <article className={`utility-card admin-post ${group.needs_review ? 'needs-review' : ''}`}>
      <div className="community-meta">
        <strong>{group.name}</strong>
        {group.department && <span className="tag-chip">{group.department}</span>}
        {!group.has_account && <span className="tag-chip">No MITra account</span>}
        {group.needs_review && (
          <span className="admin-alert-tag">
            <ShieldAlert /> Auto-suspended · needs review
          </span>
        )}
        <time>latest {group.latest}</time>
      </div>
      <div className="admin-post-stats">
        <span>
          <b>{group.reporters}</b>
          {!closed && `/${templates.threshold}`} different reporter{group.reporters === 1 ? '' : 's'}
        </span>
        {group.has_account && (
          <span>
            <b>{group.warnings}</b> previous warning{group.warnings === 1 ? '' : 's'}
          </span>
        )}
        {group.suspension && (
          <span className="admin-suspended-note">
            <Ban /> Suspended {endsLabel(group.suspension.ends_at)} · {sourceLabel(group.suspension)}
          </span>
        )}
      </div>
      <div className="tag-row">
        {group.reasons.map(([r, n]) => (
          <span key={r} className="tag-chip">
            {r} × {n}
          </span>
        ))}
      </div>
      <ul className="report-notes">
        {group.reports.map((r) => (
          <li key={r.id}>
            <span className="report-reason">{r.reason}</span>
            {r.note ? <q>{r.note}</q> : <em>No note</em>}
            <time>{r.time}</time>
            {closed && r.decision && (
              <span className="tag-chip">
                {r.decision}
                {r.decided_by ? ` · ${r.decided_by}` : ''}
              </span>
            )}
          </li>
        ))}
      </ul>
      {!closed && <DecisionPanel group={group} templates={templates} onDecided={act} />}
    </article>
  )
}

function LiftControl({ name, onLift }: { name: string; onLift: (note: string) => Promise<void> }) {
  const [open, setOpen] = useState(false)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  if (!open) {
    return (
      <div className="admin-actions">
        <button className="network-action connected" onClick={() => setOpen(true)}>
          <CheckCircle2 /> Lift suspension
        </button>
      </div>
    )
  }
  return (
    <div className="admin-composer">
      <p className="report-privacy">Lift {name}&apos;s suspension now? They get full access back and are notified.</p>
      <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Optional message to the student" maxLength={300} autoFocus />
      <div className="composer-actions">
        <button className="text-button" onClick={() => setOpen(false)}>
          Cancel
        </button>
        <button
          className="community-ask-btn small"
          disabled={busy}
          onClick={async () => {
            setBusy(true)
            await onLift(note.trim())
            setBusy(false)
            setOpen(false)
          }}
        >
          Lift suspension
        </button>
      </div>
    </div>
  )
}

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

function AdminReportsInner() {
  const params = useSearchParams()
  const initialTab = params.get('tab') === 'pleas' ? 'pleas' : 'open'
  const [tab, setTab] = useState<'open' | 'closed' | 'suspended' | 'pleas'>(initialTab)
  const [groups, setGroups] = useState<ReportGroup[]>([])
  const [suspensions, setSuspensions] = useState<Awaited<ReturnType<typeof safetyApi.suspensions>>['suspensions']>([])
  const [pleasTab, setPleasTab] = useState<'pending' | 'decided'>('pending')
  const [pleas, setPleas] = useState<AdminPlea[]>([])
  const [appeals, setAppeals] = useState<AdminAppeal[]>([])
  const [templates, setTemplates] = useState<Templates>({ warnings: [], days: [1, 3, 7, 30], threshold: 10 })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const handleError = useAdminError(setError)

  const load = useCallback(async () => {
    try {
      if (tab === 'suspended') setSuspensions((await safetyApi.suspensions()).suspensions)
      else if (tab === 'pleas') {
        const [p, a] = await Promise.all([safetyApi.pleas(pleasTab), safetyApi.appeals(pleasTab)])
        setPleas(p.pleas)
        setAppeals(a.appeals)
      } else setGroups((await safetyApi.reports(tab)).groups)
      setError(null)
    } catch (e) {
      handleError(e)
    } finally {
      setLoading(false)
    }
  }, [tab, pleasTab, handleError])

  useEffect(() => {
    setLoading(true)
    load()
  }, [load])

  useEffect(() => {
    safetyApi
      .templates()
      .then((t) => setTemplates({ warnings: t.warning_templates, days: t.suspension_days, threshold: t.auto_suspend_reporters }))
      .catch(handleError)
  }, [handleError])

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
          <p className="section-kicker">ADMIN · REPORTS</p>
          <h1>Reported accounts.</h1>
          <p className="view-sub">
            Decide on each account: innocent, a warning, or a suspension. Accounts reported by {templates.threshold} different students are
            suspended automatically and wait here for review.
          </p>
        </div>
      </div>

      <div className="utility-card admin-now">
        <Lock />
        <div>
          <strong>Private chats stay private</strong>
          <p>You only see the reason each student chose and the note they wrote. Messages are never sent to MITra, and reporters stay anonymous.</p>
        </div>
      </div>

      <div className="discover-tabs">
        <button className={tab === 'open' ? 'active' : ''} onClick={() => setTab('open')}>
          Open
        </button>
        <button className={tab === 'closed' ? 'active' : ''} onClick={() => setTab('closed')}>
          Decided
        </button>
        <button className={tab === 'suspended' ? 'active' : ''} onClick={() => setTab('suspended')}>
          Active suspensions
        </button>
        <button className={tab === 'pleas' ? 'active' : ''} onClick={() => setTab('pleas')}>
          Pleas & appeals
        </button>
      </div>

      {error && <p className="community-error">{error}</p>}
      <div className="admin-post-list">
        {loading && <p className="view-sub">Loading…</p>}
        {!loading && tab !== 'suspended' && tab !== 'pleas' && groups.map((g) => <GroupCard key={g.target} group={g} templates={templates} closed={tab === 'closed'} act={act} />)}
        {!loading && tab !== 'suspended' && tab !== 'pleas' && groups.length === 0 && !error && (
          <p className="view-sub">{tab === 'open' ? 'No open reports. 🎉' : 'No decisions yet.'}</p>
        )}
        {!loading &&
          tab === 'suspended' &&
          suspensions.map((s) => (
            <article key={s.id} className="utility-card admin-post">
              <div className="community-meta">
                <strong>{s.name}</strong>
                <span className="admin-suspended-note">
                  <Ban /> Suspended {endsLabel(s.ends_at)}
                </span>
                <time>since {s.since}</time>
                {s.plea && <span className="tag-chip">plea {s.plea}</span>}
              </div>
              <p className="admin-post-body">
                {s.reason} · {sourceLabel(s)}
              </p>
              <LiftControl name={s.name} onLift={(note) => act(() => safetyApi.lift(s.id, note))} />
            </article>
          ))}
        {!loading && tab === 'suspended' && suspensions.length === 0 && !error && <p className="view-sub">No one is suspended right now.</p>}

        {tab === 'pleas' && (
          <>
            <div className="discover-tabs" role="group" aria-label="Pleas & appeals status">
              <button className={pleasTab === 'pending' ? 'active' : ''} onClick={() => setPleasTab('pending')}>
                Waiting
              </button>
              <button className={pleasTab === 'decided' ? 'active' : ''} onClick={() => setPleasTab('decided')}>
                Decided
              </button>
            </div>
            {!loading && (
              <>
                <h3 className="insights-heading first">Suspension pleas</h3>
                {pleas.map((p) => (
                  <PleaCard key={p.id} plea={p} decided={pleasTab === 'decided'} act={act} />
                ))}
                {!error && pleas.length === 0 && <p className="view-sub">{pleasTab === 'pending' ? 'No pleas waiting.' : 'No decided pleas yet.'}</p>}
                <h3 className="insights-heading">Disabled-account appeals</h3>
                {appeals.map((a) => (
                  <AppealCard key={a.id} appeal={a} decided={pleasTab === 'decided'} act={act} />
                ))}
                {!error && appeals.length === 0 && <p className="view-sub">{pleasTab === 'pending' ? 'No appeals waiting.' : 'No decided appeals yet.'}</p>}
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default function AdminReportsPage() {
  return (
    <Suspense fallback={null}>
      <AdminReportsInner />
    </Suspense>
  )
}
