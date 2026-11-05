'use client'

import type { AuthResponse, BackendUser } from '@/lib/api'
import { defaultProfile, type Profile } from '@/lib/mock-data'

// Student and admin sign-ins are separate identities (a learner ID vs a personal admin
// email), so each has its own session and signing in to one never replaces the other.
const KEY = 'mitra_session'
const ADMIN_KEY = 'mitra_admin_session'
const PROFILE_KEY = 'mitra_profile'

export type Session = {
  learnerId: string
  name: string
  // Signed session token from the backend (Authorization: Bearer <token>)
  token: string
  user: BackendUser
}

function read(key: string): Session | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(key)
    const session = raw ? (JSON.parse(raw) as Session) : null
    // Sessions saved by the old demo login have no token — treat them as signed out
    return session?.token ? session : null
  } catch {
    return null
  }
}

/** The student session used by the MITra app. */
export function getSession(): Session | null {
  const s = read(KEY)
  // Before the split, an admin sign-in was stored here; it isn't a student session.
  return s && s.user.role !== 'admin' ? s : null
}

/**
 * A storage key for data that belongs to the signed-in student (their network, activity),
 * so a second account on the same browser doesn't inherit the first one's people.
 */
export function accountKey(base: string): string {
  const id = getSession()?.user.id
  return id ? `${base}:${id}` : base
}

export function setSession(session: Session) {
  localStorage.setItem(KEY, JSON.stringify(session))
}

export function clearSession() {
  localStorage.removeItem(KEY)
}

/** The admin session used only by the admin console. */
export function getAdminSession(): Session | null {
  const s = read(ADMIN_KEY)
  return s && s.user.role === 'admin' ? s : null
}

export function startAdminSession({ access_token, user }: AuthResponse) {
  localStorage.setItem(ADMIN_KEY, JSON.stringify({ learnerId: user.email, name: user.name, token: access_token, user }))
}

export function clearAdminSession() {
  localStorage.removeItem(ADMIN_KEY)
}

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]!.toUpperCase())
    .join('')
}

/**
 * Stores the backend session and fills the local profile (used by the sidebar, home,
 * chat and settings) with the signed-in student's real details. Avatar and interests
 * are kept if the same student signs in again on this browser.
 */
export function startSession({ access_token, user }: AuthResponse) {
  const learnerId = user.learner_id ?? user.email
  setSession({ learnerId, name: user.name, token: access_token, user })

  let previous: Profile | null = null
  try {
    const raw = localStorage.getItem(PROFILE_KEY)
    previous = raw ? (JSON.parse(raw) as Profile) : null
  } catch {}
  const sameStudent = previous?.learnerId === learnerId

  const profile: Profile = {
    name: user.name,
    initials: initials(user.name),
    learnerId,
    regNumber: user.registration_number ?? '',
    branch: user.department ?? defaultProfile.branch,
    semester: user.academic_year ?? '',
    avatar: sameStudent && previous ? previous.avatar : defaultProfile.avatar,
    interests: sameStudent && previous ? previous.interests : defaultProfile.interests,
  }
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile))
}
