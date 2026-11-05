'use client'

import Link from 'next/link'
import { Check, Clock, MessageCircle, UserCheck, UserMinus, UserPlus, UserX, X } from 'lucide-react'
import type { NetworkPerson } from '@/lib/mock-data'

export function NetworkPersonCard({
  person,
  onConnect,
  onWithdraw,
  onAccept,
  onIgnore,
  onMessage,
  onDismiss,
  onRemove,
  unreadCount = 0,
}: {
  person: NetworkPerson
  onConnect?: () => void
  onWithdraw?: () => void
  onAccept?: () => void
  onIgnore?: () => void
  onMessage?: () => void
  // The corner ✕ only ever means "not interested" in a suggestion
  onDismiss?: () => void
  // Removing a connection gets its own labelled button
  onRemove?: () => void
  unreadCount?: number // unread private messages from this connection
}) {
  return (
    <article className="network-card">
      {person.status === 'suggested' && onDismiss && (
        <button className="network-dismiss" onClick={onDismiss} aria-label="Not interested" title="Not interested">
          <X />
        </button>
      )}
      <Link href={`/network/${encodeURIComponent(person.id)}`} className="network-card-link" aria-label={`View ${person.name}'s profile`}>
        <div className="network-avatar">{person.initials}</div>
        <strong>{person.name}</strong>
        {person.accountId ? <span className="account-badge">On MITra</span> : <span className="account-badge sample">Sample</span>}
        <span className="network-meta">
          {[person.branch, person.semester].filter(Boolean).join(' · ')}
        </span>
        <p className="network-caption">
          {person.sharedInterests.length > 0 ? `Also into ${person.sharedInterests.join(', ')}` : 'Student at MIT Manipal'}
        </p>
      </Link>
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
        <div className="network-action-row">
          <button className="network-action connected" onClick={onMessage}>
            <MessageCircle /> Message
            {unreadCount > 0 && <span className="nav-badge inline">{unreadCount}</span>}
          </button>
          {onRemove && (
            <button className="network-action remove" onClick={onRemove}>
              <UserMinus /> Remove
            </button>
          )}
        </div>
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
