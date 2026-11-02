'use client'

import { useEffect, useState } from 'react'

/**
 * Local-storage backed useState. There is no backend yet, so this is how
 * mock data (votes, saved items, connections, tasks, profile edits) survives
 * navigation between routes instead of resetting on every page.
 */
export function useLocalState<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(initial)
  // State, not a ref: the save effect must wait for the render that applies the
  // stored value, otherwise it overwrites storage with `initial` on first mount.
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    try {
      const raw = localStorage.getItem(key)
      if (raw) setValue(JSON.parse(raw))
    } catch {}
    setLoaded(true)
  }, [key])

  useEffect(() => {
    if (!loaded) return
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch {}
  }, [key, value, loaded])

  return [value, setValue] as const
}
