'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowUpRight, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { AuthFrame } from '@/components/auth-frame'
import { adminSendOtp, adminVerifyOtp } from '@/lib/api'
import { startAdminSession } from '@/lib/session'
import { RESEND_COOLDOWN_SECONDS, useCountdown } from '@/lib/use-countdown'

export default function AdminLoginPage() {
  const router = useRouter()
  const [step, setStep] = useState<'email' | 'otp'>('email')
  const [email, setEmail] = useState('')
  const [sentTo, setSentTo] = useState('')
  const [otp, setOtp] = useState('')
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [cooldown, setCooldown] = useCountdown()

  async function sendCode() {
    const res = await adminSendOtp(email.trim())
    setSentTo(res.masked_email ?? email.trim())
    setCooldown(RESEND_COOLDOWN_SECONDS)
  }

  async function submitEmail(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim()) {
      setError('Enter your admin email.')
      return
    }
    setError('')
    setLoading(true)
    try {
      await sendCode()
      setOtp('')
      setNotice('')
      setStep('otp')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function verifyOtp(e: React.FormEvent) {
    e.preventDefault()
    if (otp.length !== 6) {
      setError('Enter the 6-digit code from your email.')
      return
    }
    setError('')
    setLoading(true)
    try {
      // Separate from any student sign-in in this browser.
      startAdminSession(await adminVerifyOtp(email.trim(), otp))
      router.replace('/admin/monitoring')
    } catch (err) {
      setError((err as Error).message)
      setLoading(false)
    }
  }

  async function resend() {
    setError('')
    setNotice('')
    try {
      await sendCode()
      setOtp('')
      setNotice('A new code is on its way.')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  if (step === 'otp') {
    return (
      <AuthFrame>
        <p className="section-kicker">ADMIN · CHECK YOUR INBOX</p>
        <h1>Enter the OTP.</h1>
        <p className="auth-sub">We&apos;ve sent a 6-digit sign-in code to {sentTo}. It expires in 10 minutes.</p>
        <form onSubmit={verifyOtp}>
          <label>
            One-time passcode
            <input
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="6-digit code"
              inputMode="numeric"
              autoComplete="one-time-code"
              autoFocus
            />
          </label>
          {notice && <p className="field-note">{notice}</p>}
          {error && <p className="field-error">{error}</p>}
          <Button className="auth-submit" size="lg" type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Open admin console'} <ArrowUpRight data-icon="inline-end" />
          </Button>
        </form>
        <button type="button" className="forgot" onClick={resend} disabled={cooldown > 0}>
          {cooldown > 0 ? `Resend code in ${cooldown}s` : 'Didn’t get it? Resend code'}
        </button>
        <button
          type="button"
          className="forgot"
          onClick={() => {
            setError('')
            setStep('email')
          }}
        >
          ← Use a different email
        </button>
      </AuthFrame>
    )
  }

  return (
    <AuthFrame>
      <p className="section-kicker">
        <ShieldCheck className="inline-icon" /> MITRA ADMIN
      </p>
      <h1>Admin sign-in.</h1>
      <p className="auth-sub">For the official MITra team only. Every admin action is logged under your name.</p>
      <form onSubmit={submitEmail}>
        <label>
          Admin email
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="username" type="email" />
        </label>
        <p className="field-note">Only the official MITra admin accounts can sign in here.</p>
        {error && <p className="field-error">{error}</p>}
        <Button className="auth-submit" size="lg" type="submit" disabled={loading}>
          {loading ? 'Sending code…' : 'Send sign-in code'} <ArrowUpRight data-icon="inline-end" />
        </Button>
      </form>
      <p className="auth-legal">
        Not an admin? <Link href="/login">Student sign-in</Link>
      </p>
    </AuthFrame>
  )
}
