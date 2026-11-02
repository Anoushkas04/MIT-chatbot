import Link from 'next/link'
import { Sparkles } from 'lucide-react'
import { Logo } from '@/components/logo'

export function AuthFrame({ children }: { children: React.ReactNode }) {
  return (
    <main className="auth-shell">
      <Link href="/" className="auth-back">
        ← Back to MITra
      </Link>
      <div className="auth-card">
        <div className="auth-brand">
          <Logo />
          <span className="auth-orb">
            <Sparkles />
          </span>
        </div>
        {children}
      </div>
      <div className="auth-side">
        <div className="quote-mark">&ldquo;</div>
        <blockquote>The best campus experiences often start with a simple question.</blockquote>
        <span>— MITra, your campus companion</span>
        <div className="auth-side-dots">
          <i />
          <i />
          <i />
        </div>
      </div>
    </main>
  )
}
