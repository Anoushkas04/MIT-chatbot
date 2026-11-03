'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Menu } from 'lucide-react'
import { Logo } from '@/components/logo'
import { Sidebar } from '@/components/sidebar'
import { SuspensionBanner } from '@/components/suspension-banner'
import { ApiError, currentUser } from '@/lib/api'
import { clearSession, getSession } from '@/lib/session'

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [checked, setChecked] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    if (!getSession()) {
      router.replace('/login')
      return
    }
    setChecked(true)
    // The stored token may have expired or been revoked (signed out elsewhere, account
    // disabled): confirm with the server and send the student back to sign-in if so.
    currentUser().catch((e) => {
      if (e instanceof ApiError && e.status === 401) {
        clearSession()
        router.replace('/login')
      }
    })
  }, [router])

  if (!checked) return null

  return (
    <main className="workspace">
      <Sidebar mobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />
      <div className="workspace-main">
        <div className="mobile-top">
          <Logo />
          <button aria-label="Open menu" onClick={() => setMobileOpen(true)}>
            <Menu />
          </button>
        </div>
        <SuspensionBanner />
        {children}
      </div>
    </main>
  )
}
