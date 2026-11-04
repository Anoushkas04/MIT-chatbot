'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Clock, MessageCircle, UserCheck, UserMinus, UserPlus, UserX, X } from 'lucide-react'
import { ConfirmDialog, type ConfirmRequest } from '@/components/confirm-dialog'
import { getPublicProfile, type ProfileEntry, type PublicProfile } from '@/lib/api'
import { accountToPerson, useNetworkPeople } from '@/lib/use-network'

function EntryList({ entries, empty }: { entries: ProfileEntry[]; empty: string }) {
  if (entries.length === 0) return <p className="view-sub">{empty}</p>
  return (
    <ul className="entries-list readonly">
      {entries.map((e) => (
        <li key={e.name}>
          <span>
            <strong>{e.name}</strong>
            {e.role && <em>{e.role}</em>}
          </span>
        </li>
      ))}
    </ul>
  )
}

export default function PersonProfilePage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const { people, error: networkError, connect, connectNew, withdraw, accept, ignore, dismiss } = useNetworkPeople()
  const [remote, setRemote] = useState<PublicProfile | null>(null)
  const [remoteState, setRemoteState] = useState<'idle' | 'loading' | 'missing' | 'error'>('idle')
  const [confirm, setConfirm] = useState<ConfirmRequest | null>(null)
  const closeConfirm = useCallback(() => setConfirm(null), [])

  const local = people.find((p) => p.id === id)
  // Registered students carry their account id; people found by search use "acc-<id>" before they're saved locally.
  const accountId = local?.accountId ?? (id.startsWith('acc-') ? id.slice(4) : undefined)

  useEffect(() => {
    if (!accountId) return
    setRemoteState('loading')
    getPublicProfile(accountId)
      .then((p) => {
        setRemote(p)
        setRemoteState('idle')
      })
      .catch((e) => setRemoteState(e?.status === 404 ? 'missing' : 'error'))
  }, [accountId])

  const person = local ?? (remote ? accountToPerson(remote) : null)

  if (!person || person.status === 'blocked' || remoteState === 'missing') {
    if (remoteState === 'loading') return <div className="view" />
    return (
      <div className="view">
        <Link href="/network" className="text-button">
          <ArrowLeft /> Back to Network
        </Link>
        <p className="view-sub profile-missing">This profile isn&apos;t available.</p>
      </div>
    )
  }

  const branch = remote?.department || person.branch
  const semester = remote?.semester ? `Sem ${remote.semester}` : person.semester
  const interests = remote?.interests.length ? remote.interests : person.sharedInterests
  const clubs = remote?.clubs ?? []
  const projects = remote?.projects ?? []
  const firstName = person.name.split(' ')[0]
  const known = Boolean(local)

  function removeConnection() {
    setConfirm({
      title: `Remove ${person!.name}?`,
      message: `${firstName} will be removed from your connections. You can find them through search and connect again later.`,
      confirmLabel: 'Remove',
      onConfirm: () => dismiss(person!.id),
    })
  }

  return (
    <div className="view person-profile">
      <Link href="/network" className="text-button">
        <ArrowLeft /> Back to Network
      </Link>

      <section className="person-hero">
        <div className="network-avatar large">{person.initials}</div>
        <div className="person-hero-info">
          <h1>{person.name}</h1>
          <p className="view-sub">{[branch, semester].filter(Boolean).join(' · ') || 'Student at MIT Manipal'}</p>
          {person.accountId && <span className="account-badge">On MITra</span>}
        </div>
        <div className="person-actions">
          {(person.status === 'suggested' || person.status === 'dismissed') && (
            <button className="network-action" onClick={() => (known ? connect(person.id) : connectNew(person))}>
              <UserPlus /> Connect
            </button>
          )}
          {person.status === 'pending' && (
            <>
              <button className="network-action pending" disabled>
                <Clock /> Requested
              </button>
              <button className="network-action ghost" onClick={() => withdraw(person.id)} aria-label="Withdraw request">
                <X />
              </button>
            </>
          )}
          {person.status === 'incoming' && (
            <>
              <button className="network-action" onClick={() => accept(person.id)}>
                <UserCheck /> Accept
              </button>
              <button className="network-action ghost" onClick={() => ignore(person.id)} aria-label="Ignore request">
                <UserX />
              </button>
            </>
          )}
          {person.status === 'connected' && (
            <>
              <button className="network-action connected" onClick={() => router.push(`/network?chat=${encodeURIComponent(person.id)}`)}>
                <MessageCircle /> Message
              </button>
              <button className="network-action remove" onClick={removeConnection}>
                <UserMinus /> Remove
              </button>
            </>
          )}
        </div>
      </section>

      {networkError && <p className="field-error">{networkError}</p>}
      {remoteState === 'error' && (
        <p className="field-error">Couldn&apos;t load {firstName}&apos;s latest profile. Showing what&apos;s saved on this device.</p>
      )}

      <div className="person-grid">
        <section className="deadline-card">
          <p className="section-kicker">DETAILS</p>
          <dl className="person-details">
            <div>
              <dt>Branch</dt>
              <dd>{branch || '—'}</dd>
            </div>
            <div>
              <dt>Semester</dt>
              <dd>{semester || '—'}</dd>
            </div>
            {remote?.academic_year && (
              <div>
                <dt>Academic year</dt>
                <dd>{remote.academic_year}</dd>
              </div>
            )}
          </dl>
          <p className="section-kicker person-subhead">INTERESTS</p>
          {interests.length > 0 ? (
            <div className="tag-row">
              {interests.map((i) => (
                <span key={i} className="tag-chip">
                  {i}
                </span>
              ))}
            </div>
          ) : (
            <p className="view-sub">No interests added yet.</p>
          )}
        </section>

        <section className="deadline-card">
          <p className="section-kicker">CLUBS</p>
          <EntryList entries={clubs} empty={`${firstName} hasn't added any clubs yet.`} />
          <p className="section-kicker person-subhead">STUDENT PROJECTS</p>
          <EntryList entries={projects} empty={`${firstName} hasn't added any student projects yet.`} />
        </section>
      </div>

      <ConfirmDialog request={confirm} onClose={closeConfirm} />
    </div>
  )
}
