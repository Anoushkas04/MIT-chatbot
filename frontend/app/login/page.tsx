'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowUpRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { AuthFrame } from '@/components/auth-frame'
import { loginSendOtp, loginVerifyOtp } from '@/lib/api'
import { startSession } from '@/lib/session'
import { RESEND_COOLDOWN_SECONDS, useCountdown } from '@/lib/use-countdown'

export default function LoginPage() {
  const router = useRouter()
  const [step, setStep] = useState<'identifier' | 'otp'>('identifier')
  const [identifier, setIdentifier] = useState('')
  const [sentTo, setSentTo] = useState('')
  const [otp, setOtp] = useState('')
  const [testOtp, setTestOtp] = useState<string | null>(null)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [cooldown, setCooldown] = useCountdown()

  async function sendCode() {
    const res = await loginSendOtp(identifier.trim())
    setSentTo(res.masked_email ?? res.learner_id)
    setTestOtp(res.test_otp ?? null)
    setCooldown(RESEND_COOLDOWN_SECONDS)
  }

  async function submitIdentifier(e: React.FormEvent) {
    e.preventDefault()
    if (!identifier.trim()) {
      setError('Enter your Learner ID or registration number.')
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
      startSession(await loginVerifyOtp(identifier.trim(), otp))
      router.replace('/home')
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
        <p className="section-kicker">CHECK YOUR INBOX</p>
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
          {testOtp && <p className="field-note">Local dev mode — no email sent. Your code is {testOtp}.</p>}
          {notice && <p className="field-note">{notice}</p>}
          {error && <p className="field-error">{error}</p>}
          <Button className="auth-submit" size="lg" type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Continue to MITra'} <ArrowUpRight data-icon="inline-end" />
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
            setStep('identifier')
          }}
        >
          ← Use a different ID
        </button>
      </AuthFrame>
    )
  }

  return (
    <AuthFrame>
      <p className="section-kicker">WELCOME BACK</p>
      <h1>Good to see you.</h1>
      <p className="auth-sub">Sign in to pick up where you left off.</p>
      <form onSubmit={submitIdentifier}>
        <label>
          Learner ID or registration number
          <input
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="MAHE Email ID or Registration Number"
            autoComplete="username"
          />
        </label>
        <p className="field-note">We&apos;ll email a one-time code to your learner email — no password needed.</p>
        {error && <p className="field-error">{error}</p>}
        {/disabled/i.test(error) && (
          <p className="field-note appeal-hint">
            Think this is a mistake?{' '}
            <Link href={`/appeal?id=${encodeURIComponent(identifier.trim())}`}>Send an appeal to the MITra team</Link>
          </p>
        )}
        <Button className="auth-submit" size="lg" type="submit" disabled={loading}>
          {loading ? 'Sending code…' : 'Send sign-in code'} <ArrowUpRight data-icon="inline-end" />
        </Button>
      </form>
      <p className="auth-legal">
        New to MITra? <Link href="/signup">Create an account</Link>
      </p>
    </AuthFrame>
  )
}
