'use client'

import type { AuthResponse, BackendUser } from '@/lib/api'
import { defaultProfile, type Profile } from '@/lib/mock-data'

const KEY = 'mitra_session'
const PROFILE_KEY = 'mitra_profile'

export type Session = {
  learnerId: string
  name: string
  // Signed session token from the backend (Authorization: Bearer <token>)
  token: string
  user: BackendUser
}

export function getSession(): Session | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(KEY)
    const session = raw ? (JSON.parse(raw) as Session) : null
    // Sessions saved by the old demo login have no token — treat them as signed out
    return session?.token ? session : null
  } catch {
    return null
  }
}

export function setSession(session: Session) {
  localStorage.setItem(KEY, JSON.stringify(session))
}

export function clearSession() {
  localStorage.removeItem(KEY)
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
