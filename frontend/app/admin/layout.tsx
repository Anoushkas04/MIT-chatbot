'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  Activity,
  ArrowLeft,
  BarChart3,
  Database,
  Flag,
  History,
  MessageSquare,
  Scale,
  ShieldCheck,
  Users,
} from 'lucide-react'
import { Logo } from '@/components/logo'
import { adminLogout } from '@/lib/api'
import { clearAdminSession, getAdminSession, type Session } from '@/lib/session'

const adminNav = [
  { label: 'Monitoring', href: '/admin/monitoring', icon: Activity },
  { label: 'Insights', href: '/admin/insights', icon: BarChart3 },
  { label: 'Community', href: '/admin/community', icon: MessageSquare },
  { label: 'Reports', href: '/admin/reports', icon: Flag },
  { label: 'Pleas & appeals', href: '/admin/pleas', icon: Scale },
  { label: 'Accounts', href: '/admin/accounts', icon: Users },
  { label: 'Dataset', href: '/admin/dataset', icon: Database },
  { label: 'Audit log', href: '/admin/audit', icon: History },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const isLogin = pathname === '/admin/login'
  const [session, setSessionState] = useState<Session | null>(null)
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    if (isLogin) return
    const s = getAdminSession()
    // The backend enforces this too; this just keeps the admin UI behind the admin sign-in.
    if (!s) {
      router.replace('/admin/login')
      return
    }
    setSessionState(s)
    setChecked(true)
  }, [isLogin, router])

  if (isLogin) return <>{children}</>
  if (!checked || !session) return null

  async function signOut() {
    // Revoke server-side too, so a copied token stops working; sign out locally regardless.
    await adminLogout().catch(() => {})
    clearAdminSession() // the student session in this browser stays signed in
    router.replace('/admin/login')
  }

  return (
    <main className="workspace admin-workspace">
      <aside className="sidebar admin-sidebar">
        <div className="sidebar-top">
          <Logo />
          <span className="admin-pill">
            <ShieldCheck /> Admin
          </span>
        </div>
        <nav className="side-nav">
          {adminNav.map((item) => (
            <Link key={item.href} href={item.href} className={pathname === item.href ? 'active' : ''}>
              <item.icon />
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <Link href="/home">
            <ArrowLeft />
            <span>Open MITra</span>
          </Link>
          <button onClick={signOut} title="Signs you out on every device">
            <span className="profile-avatar small admin-avatar">{(session.user.name || '?')[0]?.toUpperCase()}</span>
            <span>Sign out{session.user.name ? ` (${session.user.name})` : ''}</span>
          </button>
        </div>
      </aside>
      <div className="workspace-main">
        {children}
      </div>
    </main>
  )
}
