'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { AlertTriangle, CheckCircle2, RefreshCw, ShieldAlert, XCircle } from 'lucide-react'
import { opsApi, type Insights, type Monitoring } from '@/lib/api'
import { useAdminError } from '@/lib/use-admin-error'

export default function AdminMonitoringPage() {
  const [data, setData] = useState<Monitoring | null>(null)
  const [gaps, setGaps] = useState<Insights['chat']['knowledge_gaps'] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [updated, setUpdated] = useState<Date | null>(null)
  const handleError = useAdminError(setError)

  const load = useCallback(async () => {
    try {
      const [monitoring, insights] = await Promise.all([opsApi.monitoring(), opsApi.insights(7)])
      setData(monitoring)
      // The only part of the old separate Insights page admins actually acted on: what the
      // chatbot couldn't answer. Everything else there was charts nobody needed day to day —
      // still computed by the same backend endpoint if that ever needs to come back.
      setGaps(insights.chat.knowledge_gaps)
      setUpdated(new Date())
      setError(null)
    } catch (e) {
      handleError(e)
    }
  }, [handleError])

  useEffect(() => {
    load()
    const t = setInterval(load, 60_000) // keep the overview fresh while it's open
    return () => clearInterval(t)
  }, [load])

  const m = data?.moderation
  const attention = m ? m.needs_review.length + (m.pending_pleas ? 1 : 0) + (m.pending_appeals ? 1 : 0) + (m.open_report_accounts ? 1 : 0) : 0

  return (
    <div className="view admin-view">
      <div className="view-header">
        <div>
          <p className="section-kicker">ADMIN · MONITORING</p>
          <h1>Platform at a glance.</h1>
          <p className="view-sub">Accounts, what needs your attention, the chatbot&apos;s knowledge and system health.</p>
        </div>
        <button className="text-button" onClick={load} title="Refresh">
          <RefreshCw /> {updated ? `Updated ${updated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Refresh'}
        </button>
      </div>
      {error && <p className="community-error">{error}</p>}

      {data && (
        <>
          <div className="stat-tiles">
            <div className="stat-tile">
              <span>Student accounts</span>
              <strong>{data.students.total}</strong>
              <small>+{data.students.new_7d} this week</small>
            </div>
            <div className="stat-tile">
              <span>Active this week</span>
              <strong>{data.students.active_7d}</strong>
              <small>posted, replied, voted or chatted</small>
            </div>
            <div className="stat-tile">
              <span>Suspended now</span>
              <strong>{data.students.suspended}</strong>
            </div>
            <div className="stat-tile">
              <span>Unanswered questions</span>
              <strong>{data.moderation.unanswered_questions}</strong>
              <Link href="/admin/community" className="inline-link">
                Answer
              </Link>
            </div>
          </div>

          <section className="monitor-section">
            <h3>
              Needs attention {attention > 0 && <span className="nav-badge inline">{attention}</span>}
            </h3>
            {attention === 0 && (
              <p className="monitor-ok">
                <CheckCircle2 /> Nothing waiting. No auto-suspensions, open reports, pleas or appeals.
              </p>
            )}
            {data.moderation.needs_review.map((n) => (
              <Link key={n.user_id} href="/admin/reports" className="attention-row urgent">
                <ShieldAlert />
                <span>
                  <strong>{n.name}</strong> was auto-suspended {n.since}: reported by {n.reporters} different students. Review it.
                </span>
              </Link>
            ))}
            {data.moderation.open_report_accounts > 0 && (
              <Link href="/admin/reports" className="attention-row">
                <AlertTriangle />
                <span>
                  {data.moderation.open_report_accounts} account{data.moderation.open_report_accounts === 1 ? ' has' : 's have'} open reports
                </span>
              </Link>
            )}
            {data.moderation.pending_appeals > 0 && (
              <Link href="/admin/reports?tab=pleas" className="attention-row">
                <AlertTriangle />
                <span>
                  {data.moderation.pending_appeals} disabled account{data.moderation.pending_appeals === 1 ? ' has' : 's have'} appealed
                </span>
              </Link>
            )}
            {data.moderation.pending_pleas > 0 && (
              <Link href="/admin/reports?tab=pleas" className="attention-row">
                <AlertTriangle />
                <span>
                  {data.moderation.pending_pleas} plea{data.moderation.pending_pleas === 1 ? '' : 's'} waiting for a decision
                </span>
              </Link>
            )}
          </section>

          {gaps && gaps.length > 0 && (
            <section className="monitor-section">
              <h3>Chatbot knowledge gaps</h3>
              <p className="view-sub">Questions it couldn&apos;t answer confidently this week. Add a document or verify a Community answer to close them.</p>
              <table className="gap-table">
                <thead>
                  <tr>
                    <th>Question</th>
                    <th>Asked</th>
                    <th>Category</th>
                  </tr>
                </thead>
                <tbody>
                  {gaps.map((g) => (
                    <tr key={g.question}>
                      <td>{g.question}</td>
                      <td>{g.times_asked}×</td>
                      <td>{g.category}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          <div className="monitor-grid">
            <section className="utility-card monitor-card">
              <h3>Platform health</h3>
              <ul className="health-list">
                {data.health.map((c) => (
                  <li key={c.key} className={c.ok ? 'ok' : c.warn_only ? 'warn' : 'bad'}>
                    {c.ok ? <CheckCircle2 /> : c.warn_only ? <AlertTriangle /> : <XCircle />}
                    <span>
                      {c.label}
                      {c.detail && <small>{c.detail}</small>}
                    </span>
                    <b>{c.ok ? 'OK' : c.warn_only ? 'Optional' : 'Fix'}</b>
                  </li>
                ))}
              </ul>
            </section>

            <section className="utility-card monitor-card">
              <h3>Chatbot knowledge</h3>
              <dl className="monitor-dl">
                <dt>Documents</dt>
                <dd>{data.dataset.files}</dd>
                <dt>Indexed chunks</dt>
                <dd>{data.dataset.chunks ?? 'No index yet'}</dd>
                <dt>Community posts used</dt>
                <dd>{data.dataset.community_posts}</dd>
                <dt>Last built</dt>
                <dd>{data.dataset.built_at ? new Date(data.dataset.built_at).toLocaleString() : '—'}</dd>
                <dt>Embedder</dt>
                <dd>{data.dataset.embedder ?? '—'}</dd>
              </dl>
              {data.dataset.rebuilding && <p className="view-sub">A rebuild is running…</p>}
              <Link href="/admin/dataset" className="utility-link">
                Open dataset →
              </Link>
            </section>

            <section className="utility-card monitor-card">
              <h3>Recent admin actions</h3>
              <ul className="recent-list">
                {data.recent_actions.map((a, i) => (
                  <li key={i}>
                    <strong>{a.admin}</strong> {a.summary}
                    <time>{a.time}</time>
                  </li>
                ))}
                {data.recent_actions.length === 0 && <li className="view-sub">No actions yet.</li>}
              </ul>
              <Link href="/admin/audit" className="utility-link">
                Full audit log →
              </Link>
            </section>
          </div>
        </>
      )}
      {!data && !error && <p className="view-sub">Loading…</p>}
    </div>
  )
}
