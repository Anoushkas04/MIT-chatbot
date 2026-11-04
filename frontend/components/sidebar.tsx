'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import {
  ArrowUpRight,
  Bell,
  CalendarDays,
  Compass,
  Handshake,
  Heart,
  LayoutDashboard,
  MessageCircle,
  MessageSquare,
  MoreHorizontal,
  Search,
  Settings,
  ShieldCheck,
  Zap,
} from 'lucide-react'
import { Logo } from '@/components/logo'
import { clearSession, getAdminSession } from '@/lib/session'
import { useLocalState } from '@/lib/use-local-state'
import { defaultProfile, type Profile } from '@/lib/mock-data'
import { countUnseenNotifications, NOTIFICATIONS_CHANGED, SERVER_KEY } from '@/lib/notifications'
import { logoutEverywhere, meApi } from '@/lib/api'

const navItems = [
  { label: 'Home', href: '/home', icon: LayoutDashboard },
  { label: 'Search', href: '/search', icon: Search },
  { label: 'Ask MITra', href: '/chat', icon: MessageCircle },
  { label: 'Discover', href: '/discover', icon: Compass },
  { label: 'Community', href: '/community', icon: MessageSquare },
  { label: 'Network', href: '/network', icon: Handshake },
  { label: 'Planner', href: '/planner', icon: CalendarDays },
  { label: 'Utilities', href: '/utilities', icon: Zap },
]

export function Sidebar({ mobileOpen, onCloseMobile }: { mobileOpen: boolean; onCloseMobile: () => void }) {
  const pathname = usePathname()
  const router = useRouter()
  const [profile] = useLocalState<Profile>('mitra_profile', defaultProfile)
  const [unread, setUnread] = useState(0)
  const [isAdmin, setIsAdmin] = useState(false)

  // The sidebar stays mounted across pages, so recount from storage on each navigation.
  useEffect(() => {
    setUnread(countUnseenNotifications())
    // Shortcut only: the admin console has its own sign-in and session.
    setIsAdmin(getAdminSession() !== null)
    // Pick up new messages from the MITra team, then recount.
    let cancelled = false
    meApi
      .notifications()
      .then((res) => {
        if (cancelled) return
        try {
          localStorage.setItem(SERVER_KEY, JSON.stringify(res.notifications))
        } catch {}
        setUnread(countUnseenNotifications())
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [pathname])

  // The notifications page clears badges as sections are visited; recount without waiting for a navigation.
  useEffect(() => {
    const recount = () => setUnread(countUnseenNotifications())
    window.addEventListener(NOTIFICATIONS_CHANGED, recount)
    return () => window.removeEventListener(NOTIFICATIONS_CHANGED, recount)
  }, [])

  async function logout() {
    // Revoke on the server too, so a copied token stops working; sign out locally regardless.
    await logoutEverywhere().catch(() => {})
    clearSession()
    router.replace('/')
  }

  return (
    <>
      {mobileOpen && <button className="mobile-backdrop" aria-label="Close menu" onClick={onCloseMobile} />}
      <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-top">
          <Logo />
        </div>
        <Link href="/settings" className="profile-mini" onClick={onCloseMobile}>
          <div className="profile-avatar" style={{ background: profile.avatar.color }}>
            {profile.avatar.emoji}
          </div>
          <div>
            <strong>{profile.name.split(' ')[0]}</strong>
            <span>
              {profile.semester} · {profile.branch.split(' ')[0] === 'Computer' ? 'CSE' : profile.branch}
            </span>
          </div>
          <MoreHorizontal />
        </Link>
        <nav className="side-nav">
          {navItems.map((item) => {
            const active = pathname === item.href
            return (
              <Link key={item.href} href={item.href} className={active ? 'active' : ''} onClick={onCloseMobile}>
                <item.icon />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>
        <div className="sidebar-section">
          <span className="side-label">SAVED</span>
          <Link href="/saved" className={pathname === '/saved' ? 'active' : ''} onClick={onCloseMobile}>
            <Heart />
            <span>Saved for later</span>
          </Link>
          <Link href="/notifications" className={pathname === '/notifications' ? 'active' : ''} onClick={onCloseMobile}>
            <Bell />
            <span>Notifications</span>
            {unread > 0 && <span className="nav-badge">{unread}</span>}
          </Link>
        </div>
        <div className="sidebar-bottom">
          {isAdmin && (
            <Link href="/admin/monitoring" className="admin-console-link" onClick={onCloseMobile}>
              <ShieldCheck />
              <span>Admin console</span>
            </Link>
          )}
          <Link href="/settings" className={pathname === '/settings' ? 'active' : ''} onClick={onCloseMobile}>
            <Settings />
            <span>Settings</span>
          </Link>
          <button onClick={logout}>
            <span className="profile-avatar small" style={{ background: profile.avatar.color }}>
              {profile.avatar.emoji}
            </span>
            <span>Sign out</span>
            <ArrowUpRight />
          </button>
        </div>
      </aside>
    </>
  )
}
