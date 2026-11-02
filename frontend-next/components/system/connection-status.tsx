'use client'

import { useCallback, useEffect, useState } from 'react'
import { getHealth } from '@/lib/api'

type ConnectionState = 'checking' | 'online' | 'offline'

export function ConnectionStatus() {
  const [state, setState] = useState<ConnectionState>('checking')

  const checkConnection = useCallback(async () => {
    setState('checking')
    try {
      const health = await getHealth()
      setState(health.status === 'ok' ? 'online' : 'offline')
    } catch {
      setState('offline')
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    getHealth()
      .then(health => {
        if (!cancelled) setState(health.status === 'ok' ? 'online' : 'offline')
      })
      .catch(() => {
        if (!cancelled) setState('offline')
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <button
      className={`connection-status ${state}`}
      type="button"
      onClick={() => void checkConnection()}
      aria-label={`Backend connection is ${state}. Activate to retry.`}
    >
      <span aria-hidden="true" />
      {state === 'checking' ? 'Checking backend' : state === 'online' ? 'Backend connected' : 'Backend unavailable'}
    </button>
  )
}

