// Class timetable: VII Semester B.Tech. AIML, School of Computer Engineering, MIT Manipal.
// Shown on the Home page under "Your day". Days are numbered as in Date.getDay() (0 = Sunday).

export type ClassSlot = { start: string; end: string; course: string }

export const TIMETABLE_LABEL = 'VII Sem B.Tech. AIML'

export const weeklyTimetable: Record<number, ClassSlot[]> = {
  1: [
    { start: '14:00', end: '15:00', course: 'PE-VI' },
    { start: '15:30', end: '16:30', course: 'PE-VII' },
  ],
  2: [
    { start: '08:00', end: '09:00', course: 'OE' },
    { start: '09:00', end: '10:00', course: 'PE-III' },
    { start: '10:30', end: '11:30', course: 'PE-IV' },
    { start: '11:30', end: '12:30', course: 'PE-V' },
  ],
  3: [
    { start: '13:00', end: '14:00', course: 'OE' },
    { start: '14:00', end: '15:00', course: 'PE-IV' },
    { start: '15:30', end: '16:30', course: 'PE-V' },
  ],
  4: [
    { start: '08:00', end: '09:00', course: 'PE-VII' },
    { start: '09:00', end: '10:00', course: 'PE-VI' },
    { start: '10:30', end: '11:30', course: 'PE-III' },
    { start: '11:30', end: '12:30', course: 'OE' },
  ],
  5: [
    { start: '14:00', end: '15:00', course: 'PE-III' },
    { start: '15:30', end: '16:30', course: 'PE-IV' },
  ],
  6: [
    { start: '08:00', end: '09:00', course: 'PE-VI' },
    { start: '09:00', end: '10:00', course: 'PE-V' },
    { start: '10:30', end: '11:30', course: 'PE-VII' },
  ],
}

export function classesOn(date: Date): ClassSlot[] {
  return weeklyTimetable[date.getDay()] ?? []
}
