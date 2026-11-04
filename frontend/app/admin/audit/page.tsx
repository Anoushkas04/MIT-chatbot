'use client'

import { useCallback, useEffect, useState } from 'react'
import { Bot, History } from 'lucide-react'
import { adminApi, type AuditEntry } from '@/lib/api'
import { useAdminError } from '@/lib/use-admin-error'

const areas = [
  { label: 'Everything', value: '' },
  { label: 'Community', value: 'community.' },
  { label: 'Reports & suspensions', value: 'safety.' },
  { label: 'Accounts', value: 'accounts.' },
  { label: 'Dataset', value: 'dataset.' },
]

function actionLabel(action: string) {
  return action.replace(/^[a-z]+\./, '').replace(/_/g, ' ')
}

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [admins, setAdmins] = useState<string[]>([])
  const [area, setArea] = useState('')
  const [admin, setAdmin] = useState('')
  const [open, setOpen] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const handleError = useAdminError(setError)

  const load = useCallback(async () => {
    try {
      const data = await adminApi.audit({ action: area, admin })
      setEntries(data.entries)
      setAdmins(data.admins)
      setError(null)
    } catch (e) {
      handleError(e)
    } finally {
      setLoading(false)
    }
  }, [area, admin, handleError])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="view admin-view">
      <div className="view-header">
        <div>
          <p className="section-kicker">ADMIN · AUDIT LOG</p>
          <h1>Who did what.</h1>
          <p className="view-sub">Every admin action and every automatic rule, newest first. Entries can&apos;t be edited or deleted.</p>
        </div>
      </div>

      <div className="audit-filters">
        <div className="tag-picker">
          {areas.map((a) => (
            <button key={a.value} className={area === a.value ? 'active' : ''} onClick={() => setArea(a.value)}>
              {a.label}
            </button>
          ))}
        </div>
        <select className="interest-select" value={admin} onChange={(e) => setAdmin(e.target.value)} aria-label="Filter by admin">
          <option value="">All admins</option>
          {admins.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="community-error">{error}</p>}
      <div className="audit-list">
        {loading && <p className="view-sub">Loading…</p>}
        {entries.map((e) => (
          <article key={e.id} className="audit-row">
            <span className={`notification-icon ${e.admin === 'System' ? 'recommendation' : 'request'}`}>{e.admin === 'System' ? <Bot /> : <History />}</span>
            <div className="audit-body">
              <div className="community-meta">
                <strong>{e.admin}</strong>
                <span className="tag-chip">{actionLabel(e.action)}</span>
                <time title={e.at ?? undefined}>{e.time}</time>
              </div>
              <p>{e.summary}</p>
              {e.details && (
                <>
                  <button className="text-button" onClick={() => setOpen(open === e.id ? null : e.id)}>
                    {open === e.id ? 'Hide details' : 'Details'}
                  </button>
                  {open === e.id && <pre className="audit-details">{JSON.stringify(e.details, null, 2)}</pre>}
                </>
              )}
            </div>
          </article>
        ))}
        {!loading && !error && entries.length === 0 && <p className="view-sub">No actions recorded yet.</p>}
      </div>
    </div>
  )
}
