'use client'

import { useEffect, useRef, useState } from 'react'

/**
 * Local-storage backed useState. There is no backend yet, so this is how
 * mock data (votes, saved items, connections, tasks, profile edits) survives
 * navigation between routes instead of resetting on every page.
 */
export function useLocalState<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(initial)
  const loaded = useRef(false)

  useEffect(() => {
    try {
      const raw = localStorage.getItem(key)
      if (raw) setValue(JSON.parse(raw))
    } catch {}
    loaded.current = true
  }, [key])

  useEffect(() => {
    if (!loaded.current) return
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch {}
  }, [key, value])

  return [value, setValue] as const
}
