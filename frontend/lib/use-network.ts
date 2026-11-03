'use client'

import { useLocalState } from './use-local-state'
import { defaultNetworkPeople, type NetworkPerson, type NetworkStatus } from './mock-data'

export function useNetworkPeople() {
  const [people, setPeople] = useLocalState<NetworkPerson[]>('mitra_network', defaultNetworkPeople)

  function setStatus(id: string, status: NetworkStatus) {
    setPeople((prev) => prev.map((p) => (p.id === id ? { ...p, status } : p)))
  }

  function connect(id: string) {
    setStatus(id, 'pending')
    setTimeout(() => setStatus(id, 'connected'), 1600)
  }

  function withdraw(id: string) {
    setStatus(id, 'suggested')
  }

  function accept(id: string) {
    setStatus(id, 'connected')
  }

  function ignore(id: string) {
    setStatus(id, 'suggested')
  }

  function dismiss(id: string) {
    setStatus(id, 'dismissed')
  }

  return { people, setPeople, connect, withdraw, accept, ignore, dismiss }
}
