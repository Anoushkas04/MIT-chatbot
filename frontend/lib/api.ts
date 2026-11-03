// Client for the MITra FastAPI backend (backend/app/routers). Request/response
// shapes mirror backend/app/schemas.py.

import { getSession } from '@/lib/session'

export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export type BackendUser = {
  id: string
  email: string
  name: string
  role: string
  learner_id: string | null
  registration_number: string | null
  admission_year: string | null
  department: string | null
  academic_year: string | null
  semester: string | null
}

export type AuthResponse = {
  access_token: string
  token_type: string
  user: BackendUser
}

export type OtpSentResponse = {
  message: string
  learner_id: string
  masked_email?: string
  // Only present when the backend runs in local dev mode without an email provider
  test_otp?: string | null
  expires_in_seconds: number
}

export type CitationDetail = {
  source: string
  snippet: string
  score: number
  document_id?: string | null
  page_number?: number | null
  retrieval_method?: string | null
  source_url?: string | null
}

export type ChatResponse = {
  text: string
  sources: string[]
  citations: CitationDetail[]
  confidence: string
  confidence_type: string
}

async function post<T>(path: string, body: unknown): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new Error("Couldn't reach the MITra server. Check your connection and try again.")
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : null
    throw new Error(detail ?? `Request failed (${res.status}). Please try again.`)
  }
  return data as T
}

async function authed<T>(method: 'GET' | 'POST', path: string, body?: unknown): Promise<T> {
  const token = getSession()?.token
  if (!token) throw new Error('Please sign in to do this.')
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new Error("Couldn't reach the MITra server. Check your connection and try again.")
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : null
    throw new Error(detail ?? `Request failed (${res.status}). Please try again.`)
  }
  return data as T
}

export function registerSendOtp(body: { name: string; registration_number: string; learner_id: string }) {
  return post<OtpSentResponse>('/api/auth/register-send-otp', body)
}

export function registerVerifyOtp(body: {
  name: string
  registration_number: string
  learner_id: string
  otp_code: string
}) {
  return post<AuthResponse>('/api/auth/register-verify-otp', body)
}

export function loginSendOtp(identifier: string) {
  return post<OtpSentResponse>('/api/auth/login-send-otp', { identifier })
}

export function loginVerifyOtp(identifier: string, otp_code: string) {
  return post<AuthResponse>('/api/auth/login-verify-otp', { identifier, otp_code })
}

export function askMitra(body: {
  message: string
  session_id: string
  department?: string | null
  semester?: string | null
}) {
  return post<ChatResponse>('/api/chat', { role: 'student', language: 'en', ...body })
}

export type PublicUser = {
  id: string
  name: string
  department: string
  semester: string
  academic_year: string
  interests: string[]
}

export type ReportReason = 'Harassment' | 'Inappropriate content' | 'Spam or scam' | 'Other'

export function searchUsers(q: string) {
  return authed<{ results: PublicUser[] }>('GET', `/api/users/search?q=${encodeURIComponent(q)}`)
}

export function reportUser(body: {
  reported_user_id?: string
  reported_name: string
  reason: ReportReason
  details?: string
  recent_messages?: string[]
}) {
  return authed<{ status: string; message: string; report_id: number }>('POST', '/api/users/report', body)
}
