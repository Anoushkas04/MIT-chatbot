'use client'

import { useState } from 'react'
import { Send } from 'lucide-react'
import { NetworkPersonCard } from '@/components/network-person-card'
import { useNetworkPeople } from '@/lib/use-network'
import { defaultMessages, type DirectMessage } from '@/lib/mock-data'
import { useLocalState } from '@/lib/use-local-state'

type Tab = 'suggested' | 'requests' | 'connections'

export default function NetworkPage() {
  const { people, connect, withdraw, accept, ignore } = useNetworkPeople()
  const [messages, setMessages] = useLocalState<Record<string, DirectMessage[]>>('mitra_messages', defaultMessages)
  const [tab, setTab] = useState<Tab>('suggested')
  const [activeChat, setActiveChat] = useState<string | null>(null)
  const [draft, setDraft] = useState('')

  const suggested = people.filter((p) => p.status === 'suggested')
  const incoming = people.filter((p) => p.status === 'incoming')
  const pending = people.filter((p) => p.status === 'pending')
  const connected = people.filter((p) => p.status === 'connected')
  const requestCount = incoming.length + pending.length

  const chatPerson = activeChat ? people.find((p) => p.id === activeChat) : null
  const thread = activeChat ? messages[activeChat] ?? [] : []

  function sendMessage() {
    if (!draft.trim() || !activeChat) return
    const msg: DirectMessage = { id: `m-${Date.now()}`, from: 'me', text: draft.trim(), time: 'Now' }
    setMessages((prev) => ({ ...prev, [activeChat]: [...(prev[activeChat] ?? []), msg] }))
    setDraft('')
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
          {suggested.map((p) => (
            <NetworkPersonCard key={p.id} person={p} onConnect={() => connect(p.id)} />
          ))}
          {suggested.length === 0 && <p className="view-sub">No new suggestions right now.</p>}
        </div>
      )}

      {tab === 'requests' && (
        <div className="network-grid">
          {incoming.map((p) => (
            <NetworkPersonCard key={p.id} person={p} onAccept={() => accept(p.id)} onIgnore={() => ignore(p.id)} />
          ))}
          {pending.map((p) => (
            <NetworkPersonCard key={p.id} person={p} onWithdraw={() => withdraw(p.id)} />
          ))}
          {requestCount === 0 && <p className="view-sub">No pending requests.</p>}
        </div>
      )}

      {tab === 'connections' && (
        <div className="network-grid">
          {connected.map((p) => (
            <NetworkPersonCard key={p.id} person={p} onMessage={() => setActiveChat(p.id)} />
          ))}
          {connected.length === 0 && <p className="view-sub">You haven&apos;t connected with anyone yet.</p>}
        </div>
      )}

      {chatPerson && (
        <div className="dm-overlay" role="dialog" aria-label={`Message ${chatPerson.name}`}>
          <div className="dm-panel">
            <div className="dm-head">
              <div className="network-avatar small">{chatPerson.initials}</div>
              <strong>{chatPerson.name}</strong>
              <button className="text-button" onClick={() => setActiveChat(null)}>
                Close
              </button>
            </div>
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
          </div>
        </div>
      )}
    </div>
  )
}
