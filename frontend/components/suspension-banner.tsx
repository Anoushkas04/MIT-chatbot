'use client'

import { useCallback, useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import { Ban } from 'lucide-react'
import { meApi, type AccountStatus } from '@/lib/api'

/** Shown across the student app while the account is suspended, with the plea form. */
export function SuspensionBanner() {
  const pathname = usePathname()
  const [status, setStatus] = useState<AccountStatus | null>(null)
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    meApi
      .status()
      .then(setStatus)
      .catch(() => {}) // offline or signed out: show nothing rather than a false alarm
  }, [])

  // Re-check on navigation so an expired or lifted suspension clears without a reload.
  useEffect(() => {
    load()
  }, [load, pathname])

  if (!status?.suspended || !status.suspension) return null
  const { suspension } = status
  const plea = suspension.plea
  const ends = suspension.ends_at ? new Date(suspension.ends_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : null

  async function send() {
    setSending(true)
    setError('')
    try {
      await meApi.plea(text.trim())
      setOpen(false)
      load()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Your plea wasn't sent.")
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="suspension-banner" role="alert">
      <Ban />
      <div className="suspension-body">
        <strong>Your account is suspended{ends ? ` until ${ends}` : ' until the MITra team reviews it'}.</strong>
        <span>
          Reason: {suspension.reason}. You can keep reading, but you can&apos;t post, reply, vote or report for now.
        </span>
        {!plea && !open && (
          <button className="text-button" onClick={() => setOpen(true)}>
            Think this is a mistake? Send a plea
          </button>
        )}
        {plea?.status === 'pending' && <span className="plea-state">Your plea was sent {plea.time}. The team will review it.</span>}
        {plea?.status === 'rejected' && (
          <span className="plea-state">
            Your plea was reviewed and the suspension stays.{plea.decision_note ? ` Note from the team: ${plea.decision_note}` : ''}
          </span>
        )}
        {open && (
          <div className="plea-form">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Explain your side to the MITra team (at least 20 characters). You can send one plea per suspension."
              maxLength={2000}
              autoFocus
            />
            {error && <p className="report-error">{error}</p>}
            <div className="composer-actions">
              <button className="text-button" onClick={() => setOpen(false)}>
                Cancel
              </button>
              <button className="community-ask-btn small" disabled={text.trim().length < 20 || sending} onClick={send}>
                {sending ? 'Sending…' : 'Send plea'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
