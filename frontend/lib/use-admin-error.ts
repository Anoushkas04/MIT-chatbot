'use client'

import { useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { ApiError } from '@/lib/api'
import { clearAdminSession } from '@/lib/session'

/**
 * Error handler for admin pages: an expired, revoked or non-admin session (401/403)
 * goes back to the admin sign-in; anything else is passed to `show` as a message.
 */
export function useAdminError(show: (message: string) => void) {
  const router = useRouter()
  return useCallback(
    (e: unknown) => {
      if (e instanceof ApiError && (e.status === 401 || e.status === 403)) {
        clearAdminSession()
        router.replace('/admin/login')
        return
      }
      show(e instanceof Error ? e.message : 'Something went wrong.')
    },
    [router, show],
  )
}
