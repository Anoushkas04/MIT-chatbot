'use client'

import { Check, Clock, MessageCircle, UserCheck, UserPlus, UserX, X } from 'lucide-react'
import type { NetworkPerson } from '@/lib/mock-data'

export function NetworkPersonCard({
  person,
  onConnect,
  onWithdraw,
  onAccept,
  onIgnore,
  onMessage,
}: {
  person: NetworkPerson
  onConnect?: () => void
  onWithdraw?: () => void
  onAccept?: () => void
  onIgnore?: () => void
  onMessage?: () => void
}) {
  return (
    <article className="network-card">
      <div className="network-avatar">{person.initials}</div>
      <strong>{person.name}</strong>
      <span className="network-meta">
        {person.branch} · {person.semester}
      </span>
      <p className="network-caption">Also into {person.sharedInterests.join(', ')}</p>
      {person.status === 'suggested' && (
        <button className="network-action" onClick={onConnect}>
          <UserPlus /> Connect
        </button>
      )}
      {person.status === 'pending' && (
        <div className="network-action-row">
          <button className="network-action pending" disabled>
            <Clock /> Requested
          </button>
          {onWithdraw && (
            <button className="network-action ghost" onClick={onWithdraw} aria-label="Withdraw request">
              <X />
            </button>
          )}
        </div>
      )}
      {person.status === 'incoming' && (
        <div className="network-action-row">
          <button className="network-action" onClick={onAccept}>
            <UserCheck /> Accept
          </button>
          <button className="network-action ghost" onClick={onIgnore} aria-label="Ignore request">
            <UserX />
          </button>
        </div>
      )}
      {person.status === 'connected' && (
        <button className="network-action connected" onClick={onMessage}>
          <MessageCircle /> Message
        </button>
      )}
    </article>
  )
}

export function NetworkStatusBadge({ status }: { status: NetworkPerson['status'] }) {
  if (status !== 'connected') return null
  return (
    <span className="network-connected-tag">
      <Check /> Connected
    </span>
  )
}
