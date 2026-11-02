'use client'

import { useEffect, useState } from 'react'

/** Seconds-remaining timer for "Resend code" — matches the backend's 45s OTP resend cooldown. */
export function useCountdown() {
  const [seconds, setSeconds] = useState(0)

  useEffect(() => {
    if (seconds <= 0) return
    const id = setTimeout(() => setSeconds((s) => s - 1), 1000)
    return () => clearTimeout(id)
  }, [seconds])

  return [seconds, setSeconds] as const
}

export const RESEND_COOLDOWN_SECONDS = 45
