'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Menu } from 'lucide-react'
import { Logo } from '@/components/logo'
import { Sidebar } from '@/components/sidebar'
import { getSession } from '@/lib/session'

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
        {children}
      </div>
    </main>
  )
}
