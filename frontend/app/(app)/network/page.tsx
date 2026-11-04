'use client'

import { useCallback, useEffect, useState } from 'react'
import { Ban, Flag, Lock, MoreHorizontal, Search, Send, X } from 'lucide-react'
import { ConfirmDialog, type ConfirmRequest } from '@/components/confirm-dialog'
import { NetworkPersonCard } from '@/components/network-person-card'
import { accountToPerson, useNetworkPeople } from '@/lib/use-network'
import { defaultMessages, type DirectMessage, type NetworkPerson } from '@/lib/mock-data'
import { useLocalState } from '@/lib/use-local-state'
import { REPORT_REASONS, reportUser, searchUsers, type PublicUser, type ReportReason } from '@/lib/api'
import { getSession } from '@/lib/session'

type Tab = 'suggested' | 'requests' | 'connections'


function matchesPerson(p: NetworkPerson, q: string) {
  return `${p.name} ${p.branch} ${p.semester} ${p.sharedInterests.join(' ')}`.toLowerCase().includes(q)
}

function ReportPanel({
  person,
  onDone,
}: {
  person: NetworkPerson
  // Blocking closes the chat, so it happens on the way out rather than mid-report.
  onDone: (block: boolean) => void
}) {
  // No default, like Instagram: the reporter has to choose why.
  const [reason, setReason] = useState<ReportReason | null>(null)
  const [note, setNote] = useState('')
  const [alsoBlock, setAlsoBlock] = useState(true)
  const [state, setState] = useState<'idle' | 'sending' | 'sent'>('idle')
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    if (!reason) return
    setState('sending')
    setError(null)
    try {
      await reportUser({
        reported_user_id: person.accountId,
        reported_name: person.name,
        reason,
        note: note.trim(),
      })
      setState('sent')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not send the report.')
      setState('idle')
    }
  }

  if (state === 'sent') {
    return (
      <div className="report-panel">
        <strong>Report sent</strong>
        <p className="view-sub">Thanks for letting us know. Our team will review it.</p>
        <div className="composer-actions">
          <button className="community-ask-btn small" onClick={() => onDone(alsoBlock)}>
            Done
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="report-panel">
      <strong>Report {person.name}</strong>
      <p className="report-privacy">Why are you reporting this account?</p>
      <div className="tag-picker">
        {REPORT_REASONS.map((r) => (
          <button key={r} className={reason === r ? 'active' : ''} onClick={() => setReason(r)}>
            {r}
          </button>
        ))}
      </div>
      <textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Tell us more in your own words (optional)" maxLength={1000} />
      <p className="report-privacy">
        <Lock /> Your chat stays private. The MITra team never sees your messages, only the reason you choose and anything you
        write here. {person.name.split(' ')[0]} won&apos;t know who reported them.
      </p>
      <label className="report-check">
        <input type="checkbox" checked={alsoBlock} onChange={(e) => setAlsoBlock(e.target.checked)} />
        Also block {person.name.split(' ')[0]}
      </label>
      {error && <p className="report-error">{error}</p>}
      <div className="composer-actions">
        <button className="text-button" onClick={() => onDone(false)}>
          Cancel
        </button>
        {/* Blocking is a local safety action, so it stays available even if the report can't be sent. */}
        {error && alsoBlock && (
          <button className="text-button" onClick={() => onDone(true)}>
            Block without reporting
          </button>
        )}
        <button className="community-ask-btn small" onClick={submit} disabled={state === 'sending' || !reason}>
          {state === 'sending' ? 'Sending...' : 'Submit report'}
        </button>
      </div>
    </div>
  )
}

export default function NetworkPage() {
  const { people, connect, withdraw, accept, ignore, dismiss, block, unblock, connectNew } = useNetworkPeople()
  const [messages, setMessages] = useLocalState<Record<string, DirectMessage[]>>('mitra_messages', defaultMessages)
  const [tab, setTab] = useState<Tab>('suggested')
  const [activeChat, setActiveChat] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const [confirm, setConfirm] = useState<ConfirmRequest | null>(null)
  const closeConfirm = useCallback(() => setConfirm(null), [])
  const [reporting, setReporting] = useState(false)
  const [showBlocked, setShowBlocked] = useState(false)
  const [query, setQuery] = useState('')
  const [accounts, setAccounts] = useState<PublicUser[]>([])
  const [accountNote, setAccountNote] = useState<string | null>(null)

  const suggested = people.filter((p) => p.status === 'suggested')
  const incoming = people.filter((p) => p.status === 'incoming')
  const pending = people.filter((p) => p.status === 'pending')
  const connected = people.filter((p) => p.status === 'connected')
  const blocked = people.filter((p) => p.status === 'blocked')
  const requestCount = incoming.length + pending.length

  const chatPerson = activeChat ? people.find((p) => p.id === activeChat && p.status === 'connected') : null
  const thread = activeChat ? messages[activeChat] ?? [] : []

  const q = query.trim().toLowerCase()
  const searching = q.length > 0

  useEffect(() => {
    if (q.length < 2) {
      setAccounts([])
      setAccountNote(null)
      return
    }
    if (!getSession()) {
      setAccounts([])
      setAccountNote('Sign in to search all students on MITra.')
      return
    }
    let cancelled = false
    const timer = setTimeout(() => {
      searchUsers(q)
        .then((res) => {
          if (cancelled) return
          setAccounts(res.results)
          setAccountNote(null)
        })
        .catch(() => {
          if (cancelled) return
          setAccounts([])
          setAccountNote("Couldn't reach the server, so only showing people already on this page.")
        })
    }, 300)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [q])

  // Accounts already in the local list (e.g. after connecting) show with their saved status.
  const known = new Set(people.map((p) => p.id))
  const blockedAccountIds = new Set(blocked.map((p) => p.accountId).filter(Boolean))
  const localResults = searching ? people.filter((p) => p.status !== 'blocked' && matchesPerson(p, q)) : []
  const localNames = new Set(localResults.map((p) => p.name.toLowerCase()))
  const accountResults = accounts
    .map(accountToPerson)
    .filter((p) => !known.has(p.id) && !blockedAccountIds.has(p.accountId) && !localNames.has(p.name.toLowerCase()))
  const results = [...localResults, ...accountResults]

  // Profile pages send "Message" here as /network?chat=<id>; open that chat once, then tidy the URL.
  useEffect(() => {
    const chatId = new URLSearchParams(window.location.search).get('chat')
    // people starts as the defaults and then loads from storage, so retry until the person appears
    if (!chatId || !people.some((p) => p.id === chatId && p.status === 'connected')) return
    setActiveChat(chatId)
    window.history.replaceState(null, '', '/network')
  }, [people])

  function closeChat() {
    setActiveChat(null)
    setMenuOpen(false)
    setReporting(false)
  }

  function blockPerson(person: NetworkPerson) {
    block(person.id)
    closeChat()
  }

  function removeConnection(person: NetworkPerson) {
    setConfirm({
      title: `Remove ${person.name}?`,
      message: `${person.name.split(' ')[0]} will be removed from your connections. You can find them through search and connect again later.`,
      confirmLabel: 'Remove',
      onConfirm: () => dismiss(person.id),
    })
  }

  function sendMessage() {
    if (!draft.trim() || !activeChat) return
    const msg: DirectMessage = { id: `m-${Date.now()}`, from: 'me', text: draft.trim(), time: 'Now' }
    setMessages((prev) => ({ ...prev, [activeChat]: [...(prev[activeChat] ?? []), msg] }))
    setDraft('')
  }

  function renderCard(p: NetworkPerson) {
    switch (p.status) {
      case 'suggested':
        return (
          <NetworkPersonCard
            key={p.id}
            person={p}
            onConnect={() => (known.has(p.id) ? connect(p.id) : connectNew(p))}
            onDismiss={known.has(p.id) ? () => dismiss(p.id) : undefined}
          />
        )
      case 'incoming':
        return (
          <NetworkPersonCard
            key={p.id}
            person={p}
            onAccept={() => accept(p.id)}
            onIgnore={() => ignore(p.id)}
          />
        )
      case 'pending':
        return <NetworkPersonCard key={p.id} person={p} onWithdraw={() => withdraw(p.id)} />
      case 'connected':
        return (
          <NetworkPersonCard
            key={p.id}
            person={p}
            onMessage={() => setActiveChat(p.id)}
            onRemove={() => removeConnection(p)}
          />
        )
      default:
        // Removed people can still be found by search and reconnected.
        return (
          <NetworkPersonCard key={p.id} person={{ ...p, status: 'suggested' }} onConnect={() => connect(p.id)} />
        )
    }
  }

  return (
    <div className="view">
      <div className="view-header">
        <div>
          <p className="section-kicker">NETWORK</p>
          <h1>Find your people.</h1>
          <p className="view-sub">Connect and message students who share your interests.</p>
        </div>
      </div>

      <div className="large-search community-search network-search">
        <Search />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search students by name, branch or interest"
          aria-label="Search people"
        />
        {searching && (
          <button className="icon-action" onClick={() => setQuery('')} aria-label="Clear search" title="Clear">
            <X size={14} />
          </button>
        )}
      </div>

      {searching ? (
        <>
          <p className="search-hint">
            {results.length} {results.length === 1 ? 'person' : 'people'}
            {accountNote && <> · {accountNote}</>}
          </p>
          <div className="network-grid">
            {results.map(renderCard)}
            {results.length === 0 && <p className="view-sub">No one matches &quot;{query.trim()}&quot;.</p>}
          </div>
        </>
      ) : (
        <>
          <div className="discover-tabs">
            <button className={tab === 'suggested' ? 'active' : ''} onClick={() => setTab('suggested')}>
              Suggested for you
            </button>
            <button className={tab === 'requests' ? 'active' : ''} onClick={() => setTab('requests')}>
              Requests {requestCount > 0 && <span className="nav-badge inline">{requestCount}</span>}
            </button>
            <button className={tab === 'connections' ? 'active' : ''} onClick={() => setTab('connections')}>
              My connections
            </button>
          </div>

          {tab === 'suggested' && (
            <div className="network-grid">
              {suggested.map(renderCard)}
              {suggested.length === 0 && <p className="view-sub">No new suggestions right now.</p>}
            </div>
          )}

          {tab === 'requests' && (
            <div className="network-grid">
              {incoming.map(renderCard)}
              {pending.map(renderCard)}
              {requestCount === 0 && <p className="view-sub">No pending requests.</p>}
            </div>
          )}

          {tab === 'connections' && (
            <div className="network-grid">
              {connected.map(renderCard)}
              {connected.length === 0 && <p className="view-sub">You haven&apos;t connected with anyone yet.</p>}
            </div>
          )}
        </>
      )}

      {blocked.length > 0 && (
        <div className="blocked-section">
          <button className="text-button" onClick={() => setShowBlocked((v) => !v)}>
            <Ban /> Blocked ({blocked.length})
          </button>
          {showBlocked && (
            <div className="blocked-list">
              {blocked.map((p) => (
                <div key={p.id} className="blocked-row">
                  <div className="network-avatar small">{p.initials}</div>
                  <strong>{p.name}</strong>
                  <button className="text-button" onClick={() => unblock(p.id)}>
                    Unblock
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {chatPerson && (
        <div className="dm-overlay" role="dialog" aria-label={`Message ${chatPerson.name}`}>
          <div className="dm-panel">
            <div className="dm-head">
              <div className="network-avatar small">{chatPerson.initials}</div>
              <strong>{chatPerson.name}</strong>
              <div className="dm-menu-wrap">
                <button className="icon-action" onClick={() => setMenuOpen((v) => !v)} aria-label="More options" title="More">
                  <MoreHorizontal size={16} />
                </button>
                {menuOpen && (
                  <div className="dm-menu" role="menu">
                    <button
                      role="menuitem"
                      onClick={() => {
                        setReporting(true)
                        setMenuOpen(false)
                      }}
                    >
                      <Flag /> Report
                    </button>
                    <button
                      role="menuitem"
                      className="danger"
                      onClick={() => {
                        setMenuOpen(false)
                        setConfirm({
                          title: `Block ${chatPerson.name}?`,
                          message: "They'll be removed from your network and you won't see their messages.",
                          confirmLabel: 'Block',
                          onConfirm: () => blockPerson(chatPerson),
                        })
                      }}
                    >
                      <Ban /> Block
                    </button>
                  </div>
                )}
              </div>
              <button className="text-button" onClick={closeChat}>
                Close
              </button>
            </div>
            {reporting ? (
              <ReportPanel
                person={chatPerson}
                onDone={(alsoBlock) => (alsoBlock ? blockPerson(chatPerson) : setReporting(false))}
              />
            ) : (
              <>
                <div className="dm-thread">
                  {thread.map((m) => (
                    <div key={m.id} className={`dm-bubble ${m.from}`}>
                      {m.text}
                    </div>
                  ))}
                  {thread.length === 0 && <p className="view-sub">Say hi to {chatPerson.name.split(' ')[0]}.</p>}
                </div>
                <div className="chat-compose dm-compose">
                  <input
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') sendMessage()
                    }}
                    placeholder={`Message ${chatPerson.name.split(' ')[0]}...`}
                  />
                  <button className="send-button" onClick={sendMessage} aria-label="Send message">
                    <Send />
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
      <ConfirmDialog request={confirm} onClose={closeConfirm} />
    </div>
  )
}
