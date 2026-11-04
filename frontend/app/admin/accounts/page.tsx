'use client'

import { useCallback, useEffect, useState } from 'react'
import { Ban, Search, UserCheck, UserX, X } from 'lucide-react'
import { opsApi, type AdminAccount } from '@/lib/api'
import { useAdminError } from '@/lib/use-admin-error'

type Filter = 'all' | 'suspended' | 'reported' | 'warned' | 'disabled'
const filters: { label: string; value: Filter }[] = [
  { label: 'All', value: 'all' },
  { label: 'Suspended', value: 'suspended' },
  { label: 'Reported', value: 'reported' },
  { label: 'Warned', value: 'warned' },
  { label: 'Disabled', value: 'disabled' },
]

export default function AdminAccountsPage() {
  const [filter, setFilter] = useState<Filter>('all')
  const [query, setQuery] = useState('')
  const [debounced, setDebounced] = useState('')
  const [accounts, setAccounts] = useState<AdminAccount[]>([])
  const [total, setTotal] = useState(0)
  const [open, setOpen] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const handleError = useAdminError(setError)

  useEffect(() => {
    const t = setTimeout(() => setDebounced(query.trim()), 300)
    return () => clearTimeout(t)
  }, [query])

  const load = useCallback(async () => {
    try {
      const data = await opsApi.accounts(debounced, filter)
      setAccounts(data.accounts)
      setTotal(data.total_students)
      setError(null)
    } catch (e) {
      handleError(e)
    } finally {
      setLoading(false)
    }
  }, [debounced, filter, handleError])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="view admin-view">
      <div className="view-header">
        <div>
          <p className="section-kicker">ADMIN · ACCOUNTS</p>
          <h1>Student accounts.</h1>
          <p className="view-sub">
            {total} registered student{total === 1 ? '' : 's'}. Warn or suspend from Reports; disable an account only for serious cases (it blocks sign-in).
          </p>
        </div>
      </div>

      <div className="community-toolbar">
        <div className="large-search community-search">
          <Search />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by name, email or registration number" aria-label="Search accounts" />
          {query && (
            <button className="icon-action" onClick={() => setQuery('')} aria-label="Clear search">
              <X size={14} />
            </button>
          )}
        </div>
      </div>
      <div className="discover-tabs">
        {filters.map((f) => (
          <button key={f.value} className={filter === f.value ? 'active' : ''} onClick={() => setFilter(f.value)}>
            {f.label}
          </button>
        ))}
      </div>
      {notice && (
        <p className="admin-notice" role="status">
          {notice}
        </p>
      )}
      {error && <p className="community-error">{error}</p>}

      <div className="accounts-table" role="table" aria-label="Student accounts">
        <div className="accounts-row head" role="row">
          <span>Student</span>
          <span>Joined</span>
          <span>Posts · replies</span>
          <span>Reports</span>
          <span>Warnings</span>
          <span>Status</span>
        </div>
        {loading && <p className="view-sub">Loading…</p>}
        {accounts.map((a) => (
          <div key={a.id} className="accounts-group">
            <button className="accounts-row" role="row" onClick={() => setOpen(open === a.id ? null : a.id)} aria-expanded={open === a.id}>
              <span className="accounts-name">
                <strong>{a.name}</strong>
                <small>{a.department || a.email}</small>
              </span>
              <span>{a.joined}</span>
              <span>
                {a.posts} · {a.replies}
              </span>
              <span>{a.open_reports ? `${a.reports} (${a.open_reports} open)` : a.reports}</span>
              <span>{a.warnings}</span>
              <span>
                {a.status !== 'active' ? (
                  <span className="admin-suspended-note">
                    <UserX /> Disabled
                  </span>
                ) : a.suspended ? (
                  <span className="admin-suspended-note">
                    <Ban /> Suspended
                  </span>
                ) : (
                  'Active'
                )}
              </span>
            </button>
            {open === a.id && (
              <dl className="monitor-dl account-detail">
                <dt>Email</dt>
                <dd>{a.email}</dd>
                <dt>Registration no.</dt>
                <dd>{a.registration_number ?? '—'}</dd>
                <dt>Guideline strikes</dt>
                <dd>{a.strikes}</dd>
                {a.suspended && (
                  <>
                    <dt>Suspension</dt>
                    <dd>
                      {a.suspended.reason} · {a.suspended.ends_at ? `until ${new Date(a.suspended.ends_at).toLocaleDateString()}` : 'until lifted'}
                    </dd>
                  </>
                )}
                <dt>Account</dt>
                <dd>
                  {confirming === a.id ? (
                    <span className="account-confirm">
                      {a.status === 'active'
                        ? `Disable ${a.name}? They won't be able to sign in at all until re-enabled.`
                        : `Re-enable ${a.name}'s account?`}{' '}
                      <button className="text-button" onClick={() => setConfirming(null)}>
                        Cancel
                      </button>
                      <button
                        className={`community-ask-btn small ${a.status === 'active' ? 'danger' : ''}`}
                        onClick={async () => {
                          setConfirming(null)
                          setNotice(null)
                          try {
                            const res = await opsApi.toggleDisabled(a.id)
                            setNotice(
                              res.new_status === 'disabled'
                                ? `${a.name}'s account is disabled. Their sessions stopped working immediately and they can't sign in until you re-enable it.`
                                : `${a.name}'s account is active again. They can sign in as normal.`,
                            )
                          } catch (e) {
                            handleError(e)
                          }
                          await load()
                        }}
                      >
                        {a.status === 'active' ? 'Disable account' : 'Re-enable'}
                      </button>
                    </span>
                  ) : (
                    <button className="network-action ghost account-toggle" onClick={() => setConfirming(a.id)}>
                      {a.status === 'active' ? <UserX /> : <UserCheck />} {a.status === 'active' ? 'Disable account' : 'Re-enable account'}
                    </button>
                  )}
                </dd>
              </dl>
            )}
          </div>
        ))}
        {!loading && !error && accounts.length === 0 && <p className="view-sub dataset-empty">No accounts match.</p>}
      </div>
    </div>
  )
}
