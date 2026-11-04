'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowUpRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { AuthFrame } from '@/components/auth-frame'
import { registerSendOtp, registerVerifyOtp } from '@/lib/api'
import { startSession } from '@/lib/session'
import { RESEND_COOLDOWN_SECONDS, useCountdown } from '@/lib/use-countdown'

const LEARNER_DOMAIN = '@learner.manipal.edu'

export default function SignupPage() {
  const router = useRouter()
  const [step, setStep] = useState<'details' | 'otp'>('details')
  const [name, setName] = useState('')
  const [learnerId, setLearnerId] = useState('')
  const [regNumber, setRegNumber] = useState('')
  const [otp, setOtp] = useState('')
  const [testOtp, setTestOtp] = useState<string | null>(null)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [cooldown, setCooldown] = useCountdown()

  const details = () => ({
    name: name.trim(),
    learner_id: learnerId.trim().toLowerCase(),
    registration_number: regNumber.trim(),
  })

  async function sendCode() {
    const res = await registerSendOtp(details())
    setTestOtp(res.test_otp ?? null)
    setCooldown(RESEND_COOLDOWN_SECONDS)
  }

  async function submitDetails(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !learnerId.trim() || !regNumber.trim()) {
      setError('Fill in every field to continue.')
      return
    }
    if (!learnerId.trim().toLowerCase().endsWith(LEARNER_DOMAIN)) {
      setError('Use your verified Manipal learner email, e.g. name.mitmpl2023@learner.manipal.edu')
      return
    }
    if (!/^(\d{9}|\d{12})$/.test(regNumber.trim())) {
      setError('Registration number must be 9 or 12 digits, e.g. 220905123.')
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
      startSession(await registerVerifyOtp({ ...details(), otp_code: otp }))
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
      setNotice(`A new code is on its way to ${details().learner_id}.`)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  if (step === 'otp') {
    return (
      <AuthFrame>
        <p className="section-kicker">VERIFY YOUR IDENTITY</p>
        <h1>Enter the OTP.</h1>
        <p className="auth-sub">
          We&apos;ve sent a 6-digit code to {details().learner_id}. It expires in 10 minutes.
        </p>
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
            {loading ? 'Verifying…' : 'Verify & continue'} <ArrowUpRight data-icon="inline-end" />
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
            setStep('details')
          }}
        >
          ← Back to details
        </button>
      </AuthFrame>
    )
  }

  return (
    <AuthFrame>
      <p className="section-kicker">START YOUR MITRA JOURNEY</p>
      <h1>Create your account.</h1>
      <p className="auth-sub">Create your student account to unlock your campus companion.</p>
      <form onSubmit={submitDetails}>
        <label>
          Full name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your Name"
            autoComplete="name"
          />
        </label>
        <label>
          Learner ID
          <input
            value={learnerId}
            onChange={(e) => setLearnerId(e.target.value)}
            placeholder="MAHE Email ID"
            autoComplete="username"
          />
        </label>
        <label>
          University registration number
          <input
            value={regNumber}
            onChange={(e) => setRegNumber(e.target.value.replace(/\D/g, '').slice(0, 12))}
            placeholder="Registration Number"
            inputMode="numeric"
          />
        </label>
        <p className="field-note">
          Use your verified Manipal learner ID. We&apos;ll email you a one-time code before your account is activated.
        </p>
        {error && <p className="field-error">{error}</p>}
        <Button className="auth-submit" size="lg" type="submit" disabled={loading}>
          {loading ? 'Sending OTP…' : 'Create account'} <ArrowUpRight data-icon="inline-end" />
        </Button>
      </form>
      <p className="auth-legal">
        Already have an account? <Link href="/login">Sign in</Link>
      </p>
    </AuthFrame>
  )
}
