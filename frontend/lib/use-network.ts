'use client'

import { useCallback, useEffect, useState } from 'react'
import { networkApi, type NetworkSnapshot, type PublicUser } from './api'
import { NOTIFICATIONS_CHANGED, SERVER_NETWORK_KEY, unreadFromSnapshot } from './notifications'
import { useLocalState } from './use-local-state'
import { defaultActivity, defaultNetworkPeople, type ActivityEvent, type NetworkPerson, type NetworkStatus } from './mock-data'

const SYNC_INTERVAL_MS = 15000

export function initialsOf(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')
}

/** A registered student from account search, as a network person (id `acc-<user id>`). */
export function accountToPerson(u: PublicUser): NetworkPerson {
  return {
    id: `acc-${u.id}`,
    accountId: u.id,
    name: u.name,
    initials: initialsOf(u.name),
    branch: u.department,
    semester: u.semester ? `Sem ${u.semester}` : u.academic_year,
    sharedInterests: u.interests,
    status: 'suggested',
  }
}

/** Applies the server's view of my connections to the local list. People without an account
 * (demo entries from earlier versions) are dropped; new suggestions are added. */
function mergeSnapshot(prev: NetworkPerson[], snap: NetworkSnapshot): NetworkPerson[] {
  const server = new Map<string, { user?: PublicUser; status: NetworkStatus }>()
  for (const u of snap.connections) server.set(u.id, { user: u, status: 'connected' })
  for (const u of snap.incoming) server.set(u.id, { user: u, status: 'incoming' })
  for (const u of snap.outgoing) server.set(u.id, { user: u, status: 'pending' })
  for (const id of snap.blocked) server.set(id, { status: 'blocked' })

  const seen = new Set<string>()
  const next = prev.filter((p) => p.accountId).map((p) => {
    seen.add(p.accountId!)
    const s = server.get(p.accountId!)
    if (s) return s.status === p.status ? p : { ...p, status: s.status }
    // No relationship on the server: they removed, declined or withdrew, or it was only ever
    // on this device (connections made before they were stored on the server). Offer Connect again.
    if (p.status === 'connected' || p.status === 'pending' || p.status === 'incoming' || p.status === 'blocked') {
      return { ...p, status: 'suggested' as const }
    }
    return p
  })
  for (const [id, s] of server) {
    if (!seen.has(id) && s.user) next.push({ ...accountToPerson(s.user), status: s.status })
  }
  // Suggestions you haven't dismissed yet; ones already in the list keep their status.
  for (const u of snap.suggested ?? []) {
    if (!seen.has(u.id) && !server.has(u.id)) next.push(accountToPerson(u))
  }
  return next
}

export function useNetworkPeople() {
  const [people, setPeople] = useLocalState<NetworkPerson[]>('mitra_network', defaultNetworkPeople)
  // Things other people did that concern you, shown on the Notifications page.
  const [activity, setActivity] = useLocalState<ActivityEvent[]>('mitra_activity', defaultActivity)
  // Unread private messages from registered students, keyed by network person id
  const [unread, setUnread] = useState<Record<string, number>>({})
  const [error, setError] = useState<string | null>(null)

  const sync = useCallback(async () => {
    let snap: NetworkSnapshot
    try {
      snap = await networkApi.snapshot()
    } catch {
      return // signed out or offline: keep what's on this device
    }
    setPeople((prev) => {
      // Requests I sent that were accepted since the last sync become "accepted" notifications
      const accepted = snap.connections.filter((u) => prev.some((p) => p.accountId === u.id && p.status === 'pending'))
      if (accepted.length > 0) {
        setActivity((a) => [
          ...accepted.map((u) => ({ id: `act-acc-${u.id}`, kind: 'accepted' as const, personId: `acc-${u.id}`, at: Date.now() })),
          ...a.filter((e) => !accepted.some((u) => e.id === `act-acc-${u.id}`)),
        ])
      }
      return mergeSnapshot(prev, snap)
    })
    setUnread(unreadFromSnapshot(snap))
    try {
      localStorage.setItem(SERVER_NETWORK_KEY, JSON.stringify(snap))
    } catch {}
    window.dispatchEvent(new Event(NOTIFICATIONS_CHANGED))
  }, [setPeople, setActivity])

  useEffect(() => {
    sync()
    const timer = setInterval(sync, SYNC_INTERVAL_MS)
    window.addEventListener('focus', sync)
    return () => {
      clearInterval(timer)
      window.removeEventListener('focus', sync)
    }
  }, [sync])

  function setStatus(id: string, status: NetworkStatus) {
    setPeople((prev) => prev.map((p) => (p.id === id ? { ...p, status } : p)))
  }

  /** Runs a server action, then updates the local status. */
  async function serverAction(id: string, action: (accountId: string) => Promise<unknown>, nextStatus: NetworkStatus) {
    const person = people.find((p) => p.id === id)
    if (person?.accountId) {
      try {
        setError(null)
        await action(person.accountId)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Something went wrong. Please try again.')
        return
      }
    }
    setStatus(id, nextStatus)
  }

  async function sendRequest(person: NetworkPerson) {
    if (!person.accountId) return
    try {
      setError(null)
      const res = await networkApi.request(person.accountId)
      setStatus(person.id, res.status === 'connected' ? 'connected' : 'pending')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not send the request. Please try again.')
    }
  }

  function connect(id: string) {
    const person = people.find((p) => p.id === id)
    if (person) sendRequest(person)
  }

  // Account search results aren't in the list yet; add them on first connect.
  function connectNew(person: NetworkPerson) {
    setPeople((prev) => (prev.some((p) => p.id === person.id) ? prev : [...prev, { ...person, status: 'suggested' }]))
    sendRequest(person)
  }

  const withdraw = (id: string) => serverAction(id, networkApi.withdraw, 'suggested')
  const accept = (id: string) => serverAction(id, networkApi.accept, 'connected')
  // Declining a request shouldn't bounce the person straight back into suggestions.
  const ignore = (id: string) => serverAction(id, networkApi.decline, 'dismissed')
  const block = (id: string) => serverAction(id, networkApi.block, 'blocked')
  const unblock = (id: string) => serverAction(id, networkApi.unblock, 'suggested')

  // Removes a connection, or hides a suggestion
  function dismiss(id: string) {
    const person = people.find((p) => p.id === id)
    if (person?.status === 'connected') return serverAction(id, networkApi.remove, 'dismissed')
    setStatus(id, 'dismissed')
  }

  return {
    // Only registered students; demo entries saved by earlier versions are hidden until the next sync drops them
    people: people.filter((p) => p.accountId),
    setPeople,
    activity,
    unread,
    error,
    refresh: sync,
    connect,
    withdraw,
    accept,
    ignore,
    dismiss,
    block,
    unblock,
    connectNew,
  }
}
