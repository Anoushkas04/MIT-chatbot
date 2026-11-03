'use client'

import Link from 'next/link'
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
  Zap,
} from 'lucide-react'
import { Logo } from '@/components/logo'
import { clearSession } from '@/lib/session'
import { useLocalState } from '@/lib/use-local-state'
import { defaultProfile, type Profile } from '@/lib/mock-data'

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

  function logout() {
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
          <Link href="/planner" onClick={onCloseMobile}>
            <Bell />
            <span>Notifications</span>
            <small className="alert-dot" />
          </Link>
        </div>
        <div className="sidebar-bottom">
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
