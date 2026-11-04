'use client'

import { Suspense, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { ArrowUpRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { AuthFrame } from '@/components/auth-frame'
import { appealSendOtp, appealSubmit, type AppealInfo } from '@/lib/api'
import { RESEND_COOLDOWN_SECONDS, useCountdown } from '@/lib/use-countdown'

function AppealStatus({ appeal, previous }: { appeal: AppealInfo | null; previous?: AppealInfo | null }) {
  if (!appeal) return <p className="auth-sub">You haven&apos;t sent an appeal yet.</p>
  return (
    <div className="appeal-status">
      {previous?.status === 'rejected' && (
        <p className="field-note">
          Your previous appeal was not accepted{previous.decision_note ? `. Note from the team: ${previous.decision_note}` : '.'}
        </p>
      )}
      {appeal.status === 'pending' && (
        <p>
          <strong>Your appeal is with the MITra team.</strong> You&apos;ll be able to sign in as soon as it&apos;s accepted, so try signing in again
          later.
        </p>
      )}
      {appeal.status === 'accepted' && (
        <p>
          <strong>Your appeal was accepted.</strong> Your account is active again. <Link href="/login">Sign in</Link>
        </p>
      )}
      {appeal.status === 'rejected' && (
        <p>
          <strong>Your appeal was not accepted.</strong>
          {appeal.decision_note ? ` Note from the team: ${appeal.decision_note}` : ''} You can send a new appeal with more detail.
        </p>
      )}
      <blockquote className="plea-text">{appeal.text}</blockquote>
    </div>
  )
}

function AppealInner() {
  const params = useSearchParams()
  const [step, setStep] = useState<'identifier' | 'write' | 'done'>('identifier')
  const [identifier, setIdentifier] = useState(params.get('id') ?? '')
  const [sentTo, setSentTo] = useState('')
  const [otp, setOtp] = useState('')
  const [text, setText] = useState('')
  const [result, setResult] = useState<{ appeal: AppealInfo | null; previous?: AppealInfo | null } | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [cooldown, setCooldown] = useCountdown()

  async function sendCode(e?: React.FormEvent) {
    e?.preventDefault()
    if (!identifier.trim()) {
      setError('Enter your Learner ID or registration number.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const res = await appealSendOtp(identifier.trim())
      setSentTo(res.masked_email)
      setCooldown(RESEND_COOLDOWN_SECONDS)
      setStep('write')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function submit(checkOnly: boolean) {
    if (otp.length !== 6) {
      setError('Enter the 6-digit code from your email.')
      return
    }
    if (!checkOnly && text.trim().length < 20) {
      setError('Please explain your side in at least 20 characters.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const res = await appealSubmit(identifier.trim(), otp, checkOnly ? '' : text.trim())
      setResult(res)
      setStep('done')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  if (step === 'done' && result) {
    return (
      <AuthFrame>
        <p className="section-kicker">YOUR APPEAL</p>
        <h1>{result.appeal?.status === 'pending' ? 'Appeal sent.' : 'Appeal status.'}</h1>
        <AppealStatus appeal={result.appeal} previous={result.previous} />
        <p className="auth-legal">
          <Link href="/login">Back to sign-in</Link>
        </p>
      </AuthFrame>
    )
  }

  if (step === 'write') {
    return (
      <AuthFrame>
        <p className="section-kicker">APPEAL · CHECK YOUR INBOX</p>
        <h1>Tell us your side.</h1>
        <p className="auth-sub">We&apos;ve sent a 6-digit code to {sentTo} to confirm it&apos;s you. It expires in 10 minutes.</p>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            submit(false)
          }}
        >
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
          <label>
            Your appeal
            <textarea
              className="appeal-textarea"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Explain why your account should be re-enabled (at least 20 characters). The MITra team will read this."
              maxLength={2000}
            />
          </label>
          {error && <p className="field-error">{error}</p>}
          <Button className="auth-submit" size="lg" type="submit" disabled={loading}>
            {loading ? 'Sending…' : 'Send appeal'} <ArrowUpRight data-icon="inline-end" />
          </Button>
        </form>
        <button type="button" className="forgot" onClick={() => submit(true)} disabled={loading}>
          Already appealed? Just check its status
        </button>
        <button type="button" className="forgot" onClick={() => sendCode()} disabled={cooldown > 0}>
          {cooldown > 0 ? `Resend code in ${cooldown}s` : 'Didn’t get it? Resend code'}
        </button>
      </AuthFrame>
    )
  }

  return (
    <AuthFrame>
      <p className="section-kicker">ACCOUNT DISABLED</p>
      <h1>Appeal to the MITra team.</h1>
      <p className="auth-sub">If your account was disabled by mistake, send the team your side. We&apos;ll email a code to your learner email first to confirm it&apos;s you.</p>
      <form onSubmit={sendCode}>
        <label>
          Learner ID or registration number
          <input value={identifier} onChange={(e) => setIdentifier(e.target.value)} placeholder="MAHE Email ID or Registration Number" autoComplete="username" />
        </label>
        {error && <p className="field-error">{error}</p>}
        <Button className="auth-submit" size="lg" type="submit" disabled={loading}>
          {loading ? 'Sending code…' : 'Send verification code'} <ArrowUpRight data-icon="inline-end" />
        </Button>
      </form>
      <p className="auth-legal">
        <Link href="/login">Back to sign-in</Link>
      </p>
    </AuthFrame>
  )
}

export default function AppealPage() {
  return (
    <Suspense fallback={null}>
      <AppealInner />
    </Suspense>
  )
}
