// Key dates from the MIT Manipal Academic Calendar 2026-27
// (minor_project_docs/MIT_Manipal_Academic_Calendar_2026-27.md, which the chatbot also answers from).
// All Sundays are holidays and are not listed.

export type AcademicEventKind = 'exam' | 'holiday' | 'fest' | 'registration' | 'academic'

export type AcademicEvent = {
  id: string
  title: string
  kind: AcademicEventKind
  start: string // YYYY-MM-DD
  end?: string // inclusive; omitted for single-day events
  days?: string[] // exact days when a range has gaps (e.g. exams skipping a weekday)
  note?: string
  listOnly?: boolean // long windows (re-tests, applications) are listed but don't colour the calendar grid
}

export const ACADEMIC_YEAR_LABEL = '2026–27'

export const academicKindLabels: Record<AcademicEventKind, string> = {
  exam: 'Exam',
  holiday: 'Holiday',
  fest: 'Fest',
  registration: 'Registration',
  academic: 'Academic',
}

// When several events share a day, the calendar cell shows the first kind in this order
export const academicKindPriority: AcademicEventKind[] = ['holiday', 'exam', 'fest', 'registration', 'academic']

export const academicEvents: AcademicEvent[] = [
  // Odd semester, July – December 2026
  { id: 'ac-makeup-results-26', title: 'Makeup exam results', kind: 'academic', start: '2026-07-06' },
  { id: 'ac-rereg-jul-26', title: 'Re-registration of lower semester courses', kind: 'registration', start: '2026-07-07', end: '2026-07-11', note: 'Maths-I & PPS / III, V, VII sem B.Tech. / I sem M.Tech., I, III sem MCA/M.Sc.' },
  { id: 'ac-hol-0718', title: 'Holiday', kind: 'holiday', start: '2026-07-18' },
  { id: 'ac-classes-1st-yr', title: 'I year B.Tech. classes start', kind: 'academic', start: '2026-07-20', note: 'Student Induction Programme 20–23 Jul' },
  { id: 'ac-classes-odd', title: 'III/V/VII sem B.Tech. & MCA/M.Sc. classes start', kind: 'academic', start: '2026-07-24' },
  { id: 'ac-hol-0815', title: 'Independence Day', kind: 'holiday', start: '2026-08-15' },
  { id: 'ac-hol-0905', title: 'Krishna Janmashtami', kind: 'holiday', start: '2026-09-05' },
  { id: 'ac-hol-0914', title: 'Vinayaka Chathurthi', kind: 'holiday', start: '2026-09-14' },
  { id: 'ac-hol-0919', title: 'Holiday', kind: 'holiday', start: '2026-09-19' },
  { id: 'ac-midterm-odd', title: 'Mid-term exams', kind: 'exam', start: '2026-09-25', end: '2026-10-01', days: ['2026-09-25', '2026-09-26', '2026-09-28', '2026-09-29', '2026-10-01'] },
  { id: 'ac-hol-1002', title: 'Gandhi Jayanthi', kind: 'holiday', start: '2026-10-02' },
  { id: 'ac-retest-apply-odd', title: 'Last date to apply for mid-term re-test', kind: 'registration', start: '2026-10-08' },
  { id: 'ac-techtatva', title: 'TechTatva', kind: 'fest', start: '2026-10-14', end: '2026-10-17', note: 'Approx. 14–16 Oct; 17 Oct is a holiday' },
  { id: 'ac-hol-1017', title: 'Holiday (TechTatva)', kind: 'holiday', start: '2026-10-17' },
  { id: 'ac-retest-odd', title: 'Mid-term re-test window', kind: 'exam', start: '2026-10-19', end: '2026-11-06', note: 'Tentative', listOnly: true },
  { id: 'ac-hol-1020', title: 'Vijayadashami', kind: 'holiday', start: '2026-10-20' },
  { id: 'ac-hol-1101', title: 'Karnataka Rajyotsava', kind: 'holiday', start: '2026-11-01' },
  { id: 'ac-hol-1109', title: 'Deepavali', kind: 'holiday', start: '2026-11-09' },
  { id: 'ac-last-day-odd', title: 'Last instructional day', kind: 'academic', start: '2026-11-10' },
  { id: 'ac-endsem-odd', title: 'End semester exams', kind: 'exam', start: '2026-11-14', end: '2026-11-28' },
  { id: 'ac-hol-1121', title: 'Holiday', kind: 'holiday', start: '2026-11-21' },
  { id: 'ac-results-odd', title: 'End semester exam results', kind: 'academic', start: '2026-12-12' },
  { id: 'ac-makeup-reg-dec', title: 'Makeup exam registration', kind: 'registration', start: '2026-12-13', end: '2026-12-15' },
  { id: 'ac-makeup-odd', title: 'Makeup exams', kind: 'exam', start: '2026-12-18', end: '2027-01-02' },
  { id: 'ac-hol-1219', title: 'Holiday', kind: 'holiday', start: '2026-12-19' },
  { id: 'ac-rereg-dec-26', title: 'Re-registration of lower semester courses', kind: 'registration', start: '2026-12-24', end: '2026-12-29', note: 'IV/VI sem B.Tech., II sem M.Tech./MCA, II/IV sem M.Sc.' },
  { id: 'ac-hol-1225', title: 'Christmas', kind: 'holiday', start: '2026-12-25' },

  // Even semester, January – May 2027 (and makeups through July)
  { id: 'ac-classes-even', title: 'Even semester classes start', kind: 'academic', start: '2027-01-02' },
  { id: 'ac-rereg-jan-27', title: 'Re-registration of I year B.Tech. courses', kind: 'registration', start: '2027-01-05', end: '2027-01-09', note: 'Except Maths-I and PPS' },
  { id: 'ac-hol-0116', title: 'Holiday', kind: 'holiday', start: '2027-01-16' },
  { id: 'ac-hol-0126', title: 'Republic Day', kind: 'holiday', start: '2027-01-26' },
  { id: 'ac-revels', title: 'REVELS', kind: 'fest', start: '2027-02-17', end: '2027-02-20', note: 'Main day 18 Feb; 20 Feb is a holiday' },
  { id: 'ac-hol-0220', title: 'Holiday (Revels)', kind: 'holiday', start: '2027-02-20' },
  { id: 'ac-midterm-even', title: 'Mid-term exams', kind: 'exam', start: '2027-03-01', end: '2027-03-06' },
  { id: 'ac-hol-0310', title: 'Ramzan', kind: 'holiday', start: '2027-03-10', note: 'Subject to change as per MAHE circular' },
  { id: 'ac-branch-change', title: 'Branch change applications', kind: 'registration', start: '2027-03-11', end: '2027-04-10', listOnly: true },
  { id: 'ac-retest-apply-even', title: 'Last date to apply for mid-term re-test', kind: 'registration', start: '2027-03-13' },
  { id: 'ac-retest-even', title: 'Mid-term re-test window', kind: 'exam', start: '2027-03-19', end: '2027-04-19', note: 'Tentative', listOnly: true },
  { id: 'ac-hol-0320', title: 'Holiday', kind: 'holiday', start: '2027-03-20' },
  { id: 'ac-hol-0322', title: 'Holi', kind: 'holiday', start: '2027-03-22', note: 'Holiday for students only' },
  { id: 'ac-hol-0326', title: 'Good Friday', kind: 'holiday', start: '2027-03-26' },
  { id: 'ac-utsav', title: 'UTSAV', kind: 'fest', start: '2027-04-05', end: '2027-04-09', note: 'Main day 7 Apr' },
  { id: 'ac-hol-0417', title: 'Holiday', kind: 'holiday', start: '2027-04-17' },
  { id: 'ac-last-day-even', title: 'Last instructional day', kind: 'academic', start: '2027-04-21' },
  { id: 'ac-endsem-even', title: 'End semester exams', kind: 'exam', start: '2027-04-24', end: '2027-05-08' },
  { id: 'ac-hol-0501', title: 'May Day', kind: 'holiday', start: '2027-05-01' },
  { id: 'ac-hol-0515', title: 'Holiday', kind: 'holiday', start: '2027-05-15' },
  { id: 'ac-hol-0517', title: 'Bakrid', kind: 'holiday', start: '2027-05-17', note: 'Students only; subject to change as per MAHE circular' },
  { id: 'ac-results-even', title: 'End semester exam results', kind: 'academic', start: '2027-05-24' },
  { id: 'ac-makeup-reg-may', title: 'Makeup exam registration', kind: 'registration', start: '2027-05-28', end: '2027-06-01' },
  { id: 'ac-makeup-even', title: 'Makeup exams', kind: 'exam', start: '2027-06-12', end: '2027-06-26' },
  { id: 'ac-hol-0619', title: 'Holiday', kind: 'holiday', start: '2027-06-19' },
  { id: 'ac-makeup-results-27', title: 'Makeup exam results', kind: 'academic', start: '2027-07-09' },
  { id: 'ac-rereg-jul-27', title: 'Re-registration of lower semester courses', kind: 'registration', start: '2027-07-10', end: '2027-07-15', note: 'Maths-I & PPS / III, V, VII sem B.Tech. / I sem M.Tech., I, III sem MCA/M.Sc.' },
  { id: 'ac-hol-0717-27', title: 'Holiday', kind: 'holiday', start: '2027-07-17' },
  { id: 'ac-classes-odd-27', title: 'Next odd semester classes start', kind: 'academic', start: '2027-07-22', note: 'III/V/VII sem B.Tech., III sem MCA/M.Sc.' },
]

export function academicEventOccursOn(event: AcademicEvent, iso: string): boolean {
  if (event.days) return event.days.includes(iso)
  return iso >= event.start && iso <= (event.end ?? event.start)
}

export function academicEventsOn(iso: string): AcademicEvent[] {
  return academicEvents.filter((e) => academicEventOccursOn(e, iso))
}

// Events overlapping the given range (inclusive ISO dates), in date order
export function academicEventsBetween(fromIso: string, toIso: string): AcademicEvent[] {
  return academicEvents
    .filter((e) => e.start <= toIso && (e.end ?? e.start) >= fromIso)
    .sort((a, b) => a.start.localeCompare(b.start))
}

// "14 Nov" or "14–28 Nov" or "18 Dec – 2 Jan"; parses the parts directly so time zones can't shift the day
export function formatAcademicRange(event: AcademicEvent): string {
  const fmt = (iso: string) => {
    const [y, m, d] = iso.split('-').map(Number)
    return { day: d, month: new Date(y, m - 1, d).toLocaleDateString('en-US', { month: 'short' }) }
  }
  const s = fmt(event.start)
  if (!event.end || event.end === event.start) return `${s.day} ${s.month}`
  const e = fmt(event.end)
  return s.month === e.month ? `${s.day}–${e.day} ${s.month}` : `${s.day} ${s.month} – ${e.day} ${e.month}`
}
