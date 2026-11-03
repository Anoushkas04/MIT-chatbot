'use client'

import { useLocalState } from './use-local-state'
import { defaultActivity, defaultNetworkPeople, type ActivityEvent, type NetworkPerson, type NetworkStatus } from './mock-data'

export function useNetworkPeople() {
  const [people, setPeople] = useLocalState<NetworkPerson[]>('mitra_network', defaultNetworkPeople)
  // Things other people did that concern you, shown on the Notifications page.
  const [activity, setActivity] = useLocalState<ActivityEvent[]>('mitra_activity', defaultActivity)

  function setStatus(id: string, status: NetworkStatus) {
    setPeople((prev) => prev.map((p) => (p.id === id ? { ...p, status } : p)))
  }

  function connect(id: string) {
    setStatus(id, 'pending')
    setTimeout(() => {
      setStatus(id, 'connected')
      setActivity((prev) => [{ id: `act-${Date.now()}`, kind: 'accepted', personId: id, at: Date.now() }, ...prev])
    }, 1600)
  }

  function withdraw(id: string) {
    setStatus(id, 'suggested')
  }

  function accept(id: string) {
    setStatus(id, 'connected')
  }

  // Declining a request shouldn't bounce the person straight back into suggestions.
  function ignore(id: string) {
    setStatus(id, 'dismissed')
  }

  function dismiss(id: string) {
    setStatus(id, 'dismissed')
  }

  function block(id: string) {
    setStatus(id, 'blocked')
  }

  function unblock(id: string) {
    setStatus(id, 'suggested')
  }

  // Account search results aren't in the list yet; add them on first connect.
  function connectNew(person: NetworkPerson) {
    setPeople((prev) => (prev.some((p) => p.id === person.id) ? prev : [...prev, { ...person, status: 'suggested' }]))
    connect(person.id)
  }

  return { people, setPeople, activity, connect, withdraw, accept, ignore, dismiss, block, unblock, connectNew }
}
