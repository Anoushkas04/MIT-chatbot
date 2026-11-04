import { Award, CalendarDays, GraduationCap, Lightbulb, Sparkles, type LucideIcon } from 'lucide-react'
import { academicEvents, ACADEMIC_YEAR_LABEL } from './academic-calendar'
import { clubs, type ClubCategory } from './clubs'

// Discover only lists source-backed items: official clubs (clubs.ts), fests from the
// academic calendar, and opportunities from official MIT notices in the document library.
// Fields a source doesn't give are left out rather than filled in.

export type DiscoveryCategory = 'club' | 'event' | 'opportunity'

export type DiscoveryItem = {
  id: string
  title: string
  type: string
  category: DiscoveryCategory
  meta: string
  tone: 'coral' | 'blue' | 'yellow' | 'green'
  icon: LucideIcon
  why: string
  clubType?: ClubCategory
  details?: string
  emails?: string[]
  url?: string | null // official web page
  sourceDoc?: string // file in the document library, downloadable from Discover
  source: string
  status?: 'upcoming' | 'tentative' | 'past'
}

function todayIST() {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' })
}

function formatRange(start: string, end?: string) {
  const fmt = (iso: string, withYear: boolean) =>
    new Date(`${iso}T00:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', ...(withYear ? { year: 'numeric' } : {}) })
  return end && end !== start ? `${fmt(start, false)} – ${fmt(end, true)}` : fmt(start, true)
}

const clubItems: DiscoveryItem[] = clubs.map((c, i) => ({
  id: c.id,
  title: c.name,
  type: 'Club',
  category: 'club',
  meta: [c.category, ...c.emails].join(' · '),
  tone: c.category === 'Technical' ? 'blue' : (['coral', 'yellow', 'green'] as const)[i % 3],
  icon: c.category === 'Technical' ? Lightbulb : Sparkles,
  why: c.description.split(/(?<=[.!?])\s/)[0] ?? '',
  clubType: c.category,
  details: c.description,
  emails: c.emails,
  url: c.url,
  source: 'MIT Manipal official clubs list',
}))

function eventItems(): DiscoveryItem[] {
  const today = todayIST()
  return academicEvents
    .filter((e) => e.kind === 'fest')
    .map((e) => {
      const past = (e.end ?? e.start) < today
      const tentative = /approx|tentative/i.test(e.note ?? '')
      return {
        id: e.id,
        title: e.title,
        type: 'Fest',
        category: 'event' as const,
        meta: `${formatRange(e.start, e.end)}${tentative ? ' (approx.)' : ''}`,
        tone: 'coral' as const,
        icon: CalendarDays,
        why: past ? 'This year’s edition is over' : e.note ?? `On the Academic Calendar ${ACADEMIC_YEAR_LABEL}`,
        details: e.note,
        source: `Academic Calendar ${ACADEMIC_YEAR_LABEL}`,
        status: past ? ('past' as const) : tentative ? ('tentative' as const) : ('upcoming' as const),
      }
    })
}

const opportunityItems: DiscoveryItem[] = [
  {
    id: 'opp-best-research',
    title: 'Best Research Performance award (UG/PG)',
    type: 'Award',
    category: 'opportunity',
    meta: 'Final-year B.Tech, M.Tech, MCA and M.Sc. students of MIT',
    tone: 'green',
    icon: Award,
    why: 'Rewards publications and patents with MIT, MAHE affiliation. No deadline is stated in the notice',
    details:
      'Recognises the best research by final-year students. Nominations are scored on Q1/Q2 and other Scopus/WoS journal papers as first author, Indian utility patents filed or granted, and conference papers, each backed by supporting documents.',
    sourceDoc: 'Best Research Performance- UG-PG Students.pdf',
    source: 'MIT notice, Director-In-Charge (July 2026)',
  },
  {
    id: 'opp-ssp',
    title: 'Student Scholarship Portal (SSP)',
    type: 'Scholarship',
    category: 'opportunity',
    meta: 'Eligible students apply through SLCM',
    tone: 'yellow',
    icon: GraduationCap,
    why: 'The Apply for SSP button appears in SLCM during the application period. Dates are set there, not in the notice',
    details:
      'Log in to SLCM; eligible students see Apply for SSP under the Applications tab between the start and end dates. You can apply once and track the status from the Student Portal home page.',
    sourceDoc: 'SSP application.pdf',
    source: 'MIT notice: SSP application procedure',
  },
]

export function getDiscoveries(): DiscoveryItem[] {
  return [...eventItems(), ...opportunityItems, ...clubItems]
}

export const discoveries = getDiscoveries()

const STOP = new Set(['and', 'the', 'for', 'with'])

/** Upcoming events and opportunities, then clubs whose description matches your interests. */
export function forYou(interests: string[], items = getDiscoveries()): DiscoveryItem[] {
  const live = items.filter((d) => d.category !== 'club' && d.status !== 'past')
  const words = interests.map((i) => ({ interest: i, words: i.toLowerCase().split(/\s+/).filter((w) => w.length > 3 && !STOP.has(w)) }))
  const matched = items
    .filter((d) => d.category === 'club')
    .map((d) => {
      const text = `${d.title} ${d.details ?? ''}`.toLowerCase()
      const hit = words.find((w) => w.words.some((x) => text.includes(x)))
      return hit ? { ...d, why: `Matches your interest in ${hit.interest}` } : null
    })
    .filter((d): d is DiscoveryItem => d !== null)
  return [...live, ...matched]
}
