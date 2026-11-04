// Client for the MITra FastAPI backend (backend/app/routers). Request/response
// shapes mirror backend/app/schemas.py.

import { getAdminSession, getSession } from '@/lib/session'
import type { CommunityComment, CommunityQuestion } from '@/lib/mock-data'

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

/** Error with the HTTP status, so callers can tell "signed out" (401/403) from other failures. */
export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

/** Admin-console calls use the admin session; everything else uses the student session. */
function tokenFor(path: string): string | undefined {
  const isAdmin = path.startsWith('/api/admin') || path.startsWith('/api/auth/admin-')
  return (isAdmin ? getAdminSession() : getSession())?.token
}

async function authed<T>(method: 'GET' | 'POST' | 'PUT' | 'DELETE', path: string, body?: unknown): Promise<T> {
  const token = tokenFor(path)
  if (!token) throw new ApiError('Please sign in to do this.', 401)
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
    throw new ApiError(detail ?? `Request failed (${res.status}). Please try again.`, res.status)
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
  // Signed in, so conversations belong to the student (and count in admin insights).
  return authed<ChatResponse>('POST', '/api/chat', { role: 'student', language: 'en', ...body })
}

export type PublicUser = {
  id: string
  name: string
  department: string
  semester: string
  academic_year: string
  interests: string[]
}

// Must match backend app/safety.py REPORT_REASONS.
export const REPORT_REASONS = [
  'Harassment or bullying',
  'Hate speech',
  'Nudity or sexual content',
  'Threats or violence',
  'Spam or scam',
  'Impersonation',
  'Self-harm concern',
  'Other',
] as const
export type ReportReason = (typeof REPORT_REASONS)[number]

export function searchUsers(q: string) {
  return authed<{ results: PublicUser[] }>('GET', `/api/users/search?q=${encodeURIComponent(q)}`)
}

export function reportUser(body: {
  reported_user_id?: string
  reported_name: string
  reason: ReportReason
  note?: string // the reporter's own words; chat messages are never sent
}) {
  return authed<{ status: string; message: string; report_id: number }>('POST', '/api/users/report', body)
}

// ---- Appeals for disabled accounts (no sign-in: identity is proven with an emailed code) ----

export type AppealInfo = { status: 'pending' | 'accepted' | 'rejected'; text: string; decision_note: string | null; sent_at: string | null }

export function appealSendOtp(identifier: string) {
  return post<{ status: string; masked_email: string; expires_in_seconds: number }>('/api/auth/appeal-send-otp', { identifier })
}

/** With text: submits an appeal. Without: just returns the latest appeal's status. */
export function appealSubmit(identifier: string, otp_code: string, text: string) {
  return post<{ status: 'submitted' | 'checked'; appeal: AppealInfo | null; previous?: AppealInfo | null }>('/api/auth/appeal', { identifier, otp_code, text })
}

// ---- Admin sign-in (allowlisted emails only) ----

export function adminSendOtp(email: string) {
  return post<OtpSentResponse>('/api/auth/admin-send-otp', { email })
}

export function adminVerifyOtp(email: string, otp_code: string) {
  return post<AuthResponse>('/api/auth/admin-verify-otp', { email, otp_code })
}

/** Revokes every session this admin has, on all devices. */
export function adminLogout() {
  return authed<{ status: string }>('POST', '/api/auth/admin-logout')
}


// ---- Community (public Q&A, stored on the backend) ----

type ApiComment = {
  id: string
  author: string
  initials: string
  time: string
  body: string
  votes: number
  my_vote: number
  replies: ApiComment[]
  edited: boolean
  deleted: boolean
  is_official: boolean
  is_mine: boolean
}

type ApiPost = Omit<ApiComment, 'replies' | 'deleted'> & {
  title: string
  tags: string[]
  answers: ApiComment[]
  verified: boolean
}

export type CommunityFeed = { questions: CommunityQuestion[]; myVotes: Record<string, 1 | -1> }

function toComment(c: ApiComment, votes: Record<string, 1 | -1>): CommunityComment {
  if (c.my_vote === 1 || c.my_vote === -1) votes[c.id] = c.my_vote
  return {
    id: c.id,
    author: c.author,
    initials: c.initials,
    time: c.time,
    body: c.body,
    votes: c.votes,
    replies: c.replies.map((r) => toComment(r, votes)),
    edited: c.edited,
    deleted: c.deleted,
    isOfficial: c.is_official,
    isMine: c.is_mine,
  }
}

function toQuestion(p: ApiPost, votes: Record<string, 1 | -1>): CommunityQuestion {
  if (p.my_vote === 1 || p.my_vote === -1) votes[p.id] = p.my_vote
  return {
    id: p.id,
    title: p.title,
    body: p.body,
    tags: p.tags,
    author: p.author,
    initials: p.initials,
    time: p.time,
    votes: p.votes,
    answers: p.answers.map((a) => toComment(a, votes)),
    edited: p.edited,
    verified: p.verified,
    isOfficial: p.is_official,
    isMine: p.is_mine,
  }
}

/** One updated question plus the viewer's votes inside it. */
function single(p: ApiPost) {
  const votes: Record<string, 1 | -1> = {}
  return { question: toQuestion(p, votes), myVotes: votes }
}

export const communityApi = {
  async list(): Promise<CommunityFeed> {
    const data = await authed<{ posts: ApiPost[] }>('GET', '/api/community/posts')
    const myVotes: Record<string, 1 | -1> = {}
    return { questions: data.posts.map((p) => toQuestion(p, myVotes)), myVotes }
  },
  async create(title: string, body: string, tags: string[]) {
    return single(await authed<ApiPost>('POST', '/api/community/posts', { title, body, tags }))
  },
  async editPost(id: string, title: string, body: string) {
    return single(await authed<ApiPost>('PUT', `/api/community/posts/${id}`, { title, body }))
  },
  deletePost(id: string) {
    return authed<{ status: string }>('DELETE', `/api/community/posts/${id}`)
  },
  async comment(postId: string, body: string, parentId?: string) {
    return single(await authed<ApiPost>('POST', `/api/community/posts/${postId}/comments`, { body, parent_id: parentId }))
  },
  async editComment(id: string, body: string) {
    return single(await authed<ApiPost>('PUT', `/api/community/comments/${id}`, { body }))
  },
  async deleteComment(id: string) {
    return single(await authed<ApiPost>('DELETE', `/api/community/comments/${id}`))
  },
  vote(target: string, value: 1 | -1 | 0) {
    return authed<{ target: string; votes: number; my_vote: number }>('POST', '/api/community/vote', { target, value })
  },
}

// ---- Notifications from MITra (server-side) ----

export type ServerNotification = {
  id: string
  category: 'official_reply' | 'post_deleted' | 'post_verified' | string
  icon: string
  title: string
  content: string
  read: boolean
  time: string
}

export type AccountStatus = {
  suspended: boolean
  warnings: number
  suspension: {
    id: number
    reason: string
    message: string
    ends_at: string | null
    plea: { status: 'pending' | 'accepted' | 'rejected' | 'closed'; text: string; decision_note: string | null; time: string } | null
  } | null
}

export const meApi = {
  status: () => authed<AccountStatus>('GET', '/api/me/status'),
  plea: (text: string) => authed<{ status: string }>('POST', '/api/me/plea', { text }),
  notifications: () => authed<{ notifications: ServerNotification[] }>('GET', '/api/me/notifications'),
  markRead: (id: string) => authed<{ status: string }>('POST', `/api/me/notifications/${id}/read`),
  markAllRead: () => authed<{ status: string }>('POST', '/api/me/notifications/read-all'),
}

// ---- Admin: community moderation and audit log ----

export type AdminDeleted = { by: string; reason: string | null; time: string } | null

export type AdminComment = {
  id: string
  author: string
  body: string
  time: string
  votes: number
  is_official: boolean
  edited: boolean
  deleted: AdminDeleted
  replies: AdminComment[]
}

export type AdminPost = {
  id: string
  title: string
  body: string
  tags: string[]
  author: string
  time: string
  votes: number
  upvotes: number
  answer_count: number
  has_official_reply: boolean
  verified: boolean
  verified_by: string | null
  in_dataset: boolean
  dataset_source: 'community_verified' | 'community_popular' | null
  deleted: AdminDeleted
  answers: AdminComment[]
}

export type AdminView = 'all' | 'unanswered' | 'popular' | 'verified' | 'dataset' | 'deleted'
export type ReplyTemplate = { key: string; label: string; text: string }

export type AuditEntry = {
  id: number
  admin: string
  action: string
  target_type: string | null
  target_id: string | null
  summary: string
  details: Record<string, unknown> | null
  time: string
  at: string | null
}

export const adminApi = {
  templates: () =>
    authed<{ reply_templates: ReplyTemplate[]; delete_reasons: string[]; popular_threshold: number }>('GET', '/api/admin/community/templates'),
  posts: (view: AdminView) =>
    authed<{ posts: AdminPost[]; counts: Record<AdminView, number> }>('GET', `/api/admin/community/posts?view=${view}`),
  reply: (postId: string, body: string, parentId?: string, templateKey?: string) =>
    authed<AdminPost>('POST', `/api/admin/community/posts/${postId}/reply`, { body, parent_id: parentId, template_key: templateKey }),
  verify: (postId: string, verified: boolean) => authed<AdminPost>('POST', `/api/admin/community/posts/${postId}/verify`, { verified }),
  deletePost: (postId: string, reason: string, note: string) =>
    authed<AdminPost>('POST', `/api/admin/community/posts/${postId}/delete`, { reason, note }),
  restorePost: (postId: string) => authed<AdminPost>('POST', `/api/admin/community/posts/${postId}/restore`),
  deleteComment: (commentId: string, reason: string, note: string) =>
    authed<AdminPost>('POST', `/api/admin/community/comments/${commentId}/delete`, { reason, note }),
  restoreComment: (commentId: string) => authed<AdminPost>('POST', `/api/admin/community/comments/${commentId}/restore`),
  audit: (params: { action?: string; admin?: string } = {}) => {
    const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v) as [string, string][]).toString()
    return authed<{ entries: AuditEntry[]; admins: string[] }>('GET', `/api/admin/audit${q ? `?${q}` : ''}`)
  },
}

// ---- Admin: reports, warnings, suspensions, pleas ----

export type AdminSuspension = {
  id: number
  source: 'auto_reports' | 'auto_strikes' | 'admin' | string
  reason: string
  since: string
  ends_at: string | null
  reviewed: boolean
  by: string
}

export type ReportGroup = {
  target: string // user id, or "name:<display name>" for people without an account
  name: string
  has_account: boolean
  department: string
  reporters: number
  reasons: [string, number][]
  warnings: number
  suspension: AdminSuspension | null
  needs_review: boolean
  latest: string
  reports: { id: number; reason: string; note: string; time: string; status: string; decision: string | null; decided_by: string | null }[]
}

export type AdminPlea = {
  id: number
  name: string
  user_id: string
  text: string
  time: string
  status: string
  decision_note: string | null
  decided_by: string | null
  suspension: Partial<AdminSuspension> & { status: string | null }
  report_reasons: [string, number][]
}

export type WarningTemplate = { key: string; label: string; text: string }

export const safetyApi = {
  templates: () =>
    authed<{ warning_templates: WarningTemplate[]; suspension_days: number[]; report_reasons: string[]; auto_suspend_reporters: number }>(
      'GET',
      '/api/admin/safety/templates',
    ),
  reports: (status: 'open' | 'closed') => authed<{ groups: ReportGroup[]; auto_suspend_reporters: number }>('GET', `/api/admin/reports?status=${status}`),
  decide: (body: {
    target: string
    decision: 'innocent' | 'warn' | 'suspend'
    warning_key?: string
    warning_text?: string
    days?: number | null
    reason?: string
  }) => authed<{ status: string }>('POST', '/api/admin/reports/decide', body),
  suspensions: () => authed<{ suspensions: (AdminSuspension & { user_id: string; name: string; plea: string | null })[] }>('GET', '/api/admin/suspensions'),
  lift: (id: number, note: string) => authed<{ status: string }>('POST', `/api/admin/suspensions/${id}/lift`, { note }),
  pleas: (status: 'pending' | 'decided') => authed<{ pleas: AdminPlea[] }>('GET', `/api/admin/pleas?status=${status}`),
  decidePlea: (id: number, accept: boolean, note: string) => authed<{ status: string }>('POST', `/api/admin/pleas/${id}/decide`, { accept, note }),
  appeals: (status: 'pending' | 'decided') => authed<{ appeals: AdminAppeal[] }>('GET', `/api/admin/appeals?status=${status}`),
  decideAppeal: (id: number, accept: boolean, note: string) => authed<{ status: string }>('POST', `/api/admin/appeals/${id}/decide`, { accept, note }),
}

export type AdminAppeal = {
  id: number
  user_id: string
  name: string
  email: string
  account_status: string | null
  text: string
  time: string
  status: string
  decision_note: string | null
  decided_by: string | null
  disabled_by: string | null
  disabled_when: string | null
}

// ---- Admin: dataset manager, monitoring, accounts, insights ----

async function authedUpload<T>(path: string, form: FormData): Promise<T> {
  const token = tokenFor(path)
  if (!token) throw new ApiError('Please sign in to do this.', 401)
  let res: Response
  try {
    // No Content-Type header: the browser sets the multipart boundary itself.
    res = await fetch(`${API_BASE}${path}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form })
  } catch {
    throw new Error("Couldn't reach the MITra server. Check your connection and try again.")
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : null
    throw new ApiError(detail ?? `Upload failed (${res.status}).`, res.status)
  }
  return data as T
}

export type DatasetFile = {
  name: string
  type: string
  supported: boolean
  size: string
  modified: string
  chunks: number | null
  version: number
  last_change: { by: string; action: string; when: string } | null
}

export type DatasetInfo = {
  files: DatasetFile[]
  index: {
    exists: boolean
    embedder: string | null
    current_embedder: string
    built_at: string | null
    total_chunks: number | null
    rebuild: { running: boolean; started_at: string | null; finished_at: string | null; error: string | null; chunks: number | null }
  }
  community_posts_in_dataset: number
  supported_extensions: string[]
  max_mb: number
}

export type HealthCheck = { key: string; label: string; ok: boolean; detail?: string; warn_only?: boolean }

export type Monitoring = {
  students: { total: number; new_7d: number; active_7d: number; suspended: number }
  moderation: {
    needs_review: { user_id: string; name: string; reporters: number; since: string }[]
    open_report_accounts: number
    pending_pleas: number
    pending_appeals: number
    unanswered_questions: number
  }
  dataset: { files: number; chunks: number | null; built_at: string | null; embedder: string | null; community_posts: number; rebuilding: boolean }
  health: HealthCheck[]
  recent_actions: { admin: string; summary: string; time: string }[]
}

export type AdminAccount = {
  id: string
  name: string
  email: string
  registration_number: string | null
  department: string
  joined: string
  posts: number
  replies: number
  reports: number
  open_reports: number
  warnings: number
  strikes: number
  status: 'active' | 'disabled' | string
  suspended: { reason: string; ends_at: string | null; source: string } | null
}

export type DayValue = { date: string; value: number }

export type Insights = {
  days: number
  chat: {
    questions: number
    per_day: DayValue[]
    low_confidence_rate: number | null
    answers: number
    topics: [string, number][]
    intents: [string, number][]
    knowledge_gaps: { question: string; times_asked: number; category: string; status: string }[]
    feedback_count: number
    avg_rating: number | null
    helpful_rate: number | null
  }
  community: {
    questions: number
    answers: number
    questions_per_day: DayValue[]
    answers_per_day: DayValue[]
    unanswered_rate: number | null
    median_hours_to_first_answer: number | null
    official_replies: number
    removed: number
    top_tags: [string, number][]
  }
  safety: { reports: number; by_reason: [string, number][]; warnings: number; suspensions: number }
  accounts: { signups: number; signups_per_day: DayValue[] }
}

export const opsApi = {
  dataset: () => authed<DatasetInfo>('GET', '/api/admin/dataset'),
  upload: (file: File, replace: boolean) => {
    const form = new FormData()
    form.append('file', file)
    form.append('replace', String(replace))
    return authedUpload<{ status: 'added' | 'replaced'; name: string; chunks: number }>('/api/admin/dataset/upload', form)
  },
  remove: (name: string) => authed<{ status: string; chunks_removed: number }>('DELETE', `/api/admin/dataset/files/${encodeURIComponent(name)}`),
  rebuild: () => authed<{ status: string }>('POST', '/api/admin/dataset/rebuild'),
  monitoring: () => authed<Monitoring>('GET', '/api/admin/monitoring'),
  toggleDisabled: (userId: string) =>
    authed<{ status: string; new_status: string }>('POST', `/api/admin/users/toggle-status?user_id=${encodeURIComponent(userId)}`),
  accounts: (q: string, filter: 'all' | 'suspended' | 'reported' | 'warned' | 'disabled') =>
    authed<{ accounts: AdminAccount[]; total_students: number }>('GET', `/api/admin/accounts?filter=${filter}${q ? `&q=${encodeURIComponent(q)}` : ''}`),
  insights: (days: 7 | 30 | 90) => authed<Insights>('GET', `/api/admin/insights?days=${days}`),
}

// ---- Session ----

/** Confirms the stored token is still valid (throws ApiError 401 if it expired or was revoked). */
export function currentUser() {
  return authed<BackendUser & { role: string }>('GET', '/api/auth/me')
}

/** Signs out on every device by revoking this account's tokens on the server. */
export function logoutEverywhere() {
  return authed<{ status: string }>('POST', '/api/auth/logout')
}

// ---- Official documents (the dataset admins manage) ----

export type LibraryHit = { source: string; title: string; type: string; snippet: string; score: number; downloadable: boolean }
export type LibraryDocument = { name: string; title: string; type: string; size: string; updated: string }

export const libraryApi = {
  search: (q: string) => authed<{ results: LibraryHit[]; indexed: boolean }>('GET', `/api/search?q=${encodeURIComponent(q)}`),
  documents: () => authed<{ documents: LibraryDocument[] }>('GET', '/api/documents'),
  /** Downloads with the session token (a plain link can't send it) and saves the file. */
  async download(name: string) {
    const token = getSession()?.token
    if (!token) throw new ApiError('Please sign in to do this.', 401)
    const res = await fetch(`${API_BASE}/api/documents/${encodeURIComponent(name)}/download`, { headers: { Authorization: `Bearer ${token}` } })
    if (!res.ok) throw new ApiError(res.status === 404 ? 'That document is no longer available.' : `Download failed (${res.status}).`, res.status)
    const url = URL.createObjectURL(await res.blob())
    const a = document.createElement('a')
    a.href = url
    a.download = name
    a.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  },
}
