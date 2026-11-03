'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import {
  ArrowLeft,
  BookOpen,
  Building2,
  CalendarDays,
  FileText,
  GraduationCap,
  HelpCircle,
  MapPin,
  Plus,
  Search,
  Trash2,
  Users,
} from 'lucide-react'
import {
  amenities,
  councilMembers,
  defaultAttendanceCourses,
  defaultGpaCourses,
  documents,
  gradeOptions,
  helpdeskContacts,
  labs,
  professors,
  type AttendanceCourse,
  type GpaCourse,
} from '@/lib/mock-data'
import { useLocalState } from '@/lib/use-local-state'

type Section = 'gpa' | 'attendance' | 'professors' | 'labs' | 'documents' | 'helpdesk' | 'council' | 'amenities'

const hubCards: { id: Section; title: string; subtitle: string; icon: typeof GraduationCap }[] = [
  { id: 'gpa', title: 'GPA Calculator', subtitle: 'Current semester estimate', icon: GraduationCap },
  { id: 'attendance', title: 'Attendance Calculator', subtitle: 'Stay above the 75% line', icon: BookOpen },
  { id: 'professors', title: 'Professors', subtitle: 'Find your professors on campus', icon: Users },
  { id: 'labs', title: 'Labs', subtitle: 'Locate department labs', icon: Building2 },
  { id: 'documents', title: 'Documents', subtitle: 'Regulations, forms & notices', icon: FileText },
  { id: 'helpdesk', title: 'Academic Helpdesk', subtitle: 'Who to contact, and when', icon: HelpCircle },
  { id: 'council', title: 'Student Council', subtitle: 'Meet your student representatives', icon: Users },
  { id: 'amenities', title: 'Amenities', subtitle: 'Food, medical, sports & more', icon: MapPin },
]

function SearchFilter({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder: string }) {
  return (
    <div className="utility-search">
      <Search />
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
    </div>
  )
}

function GpaSection() {
  const [courses, setCourses] = useLocalState<GpaCourse[]>('mitra_gpa_courses', defaultGpaCourses)
  const [formOpen, setFormOpen] = useState(false)
  const [course, setCourse] = useState('')
  const [credits, setCredits] = useState(3)
  const [grade, setGrade] = useState(gradeOptions[0].grade)

  const totalCredits = courses.reduce((a, c) => a + c.credits, 0)
  const gpa = totalCredits === 0 ? '0.00' : (courses.reduce((a, c) => a + c.value * c.credits, 0) / totalCredits).toFixed(2)

  function addCourse() {
    if (!course.trim()) return
    const g = gradeOptions.find((g) => g.grade === grade) ?? gradeOptions[0]
    setCourses((prev) => [...prev, { id: `g-${Date.now()}`, course: course.trim(), grade: g.grade, value: g.value, credits }])
    setCourse('')
    setCredits(3)
    setFormOpen(false)
  }

  function removeCourse(id: string) {
    setCourses((prev) => prev.filter((c) => c.id !== id))
  }

  return (
    <section className="utility-card gpa-card">
      <div className="utility-heading">
        <div className="utility-icon">
          <GraduationCap />
        </div>
        <div>
          <h3>GPA calculator</h3>
          <p>Current semester estimate</p>
        </div>
      </div>
      <div className="gpa-score">
        <strong>{gpa}</strong>
        <span>/ 10.0 estimated GPA</span>
      </div>
      <div className="grade-rows">
        {courses.map((c) => (
          <div key={c.id}>
            <span>{c.course}</span>
            <b>{c.grade}</b>
            <small>{c.credits} credits</small>
            <button className="icon-ghost" onClick={() => removeCourse(c.id)} aria-label={`Remove ${c.course}`}>
              <Trash2 />
            </button>
          </div>
        ))}
      </div>
      {formOpen ? (
        <div className="planner-form inline-form">
          <input value={course} onChange={(e) => setCourse(e.target.value)} placeholder="Course name" autoFocus />
          <select value={credits} onChange={(e) => setCredits(Number(e.target.value))}>
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {n} credits
              </option>
            ))}
          </select>
          <select value={grade} onChange={(e) => setGrade(e.target.value)}>
            {gradeOptions.map((g) => (
              <option key={g.grade} value={g.grade}>
                {g.grade}
              </option>
            ))}
          </select>
          <div className="composer-actions">
            <button className="text-button" onClick={() => setFormOpen(false)}>
              Cancel
            </button>
            <button className="community-ask-btn small" onClick={addCourse}>
              Add
            </button>
          </div>
        </div>
      ) : (
        <button className="utility-link" onClick={() => setFormOpen(true)}>
          <Plus /> Add course
        </button>
      )}
    </section>
  )
}

function AttendanceSection() {
  const [courses, setCourses] = useLocalState<AttendanceCourse[]>('mitra_attendance_courses', defaultAttendanceCourses)
  const [formOpen, setFormOpen] = useState(false)
  const [course, setCourse] = useState('')

  const totalHeld = courses.reduce((a, c) => a + c.held, 0)
  const totalAttended = courses.reduce((a, c) => a + c.attended, 0)
  const overall = totalHeld === 0 ? 0 : Math.round((totalAttended / totalHeld) * 100)

  function update(id: string, field: 'held' | 'attended', value: number) {
    setCourses((prev) => prev.map((c) => (c.id === id ? { ...c, [field]: Math.max(0, value) } : c)))
  }

  function addCourse() {
    if (!course.trim()) return
    setCourses((prev) => [...prev, { id: `a-${Date.now()}`, course: course.trim(), held: 0, attended: 0 }])
    setCourse('')
    setFormOpen(false)
  }

  function removeCourse(id: string) {
    setCourses((prev) => prev.filter((c) => c.id !== id))
  }

  return (
    <section className="utility-card attendance-card wide">
      <div className="utility-heading">
        <div className="utility-icon coral-bg">
          <BookOpen />
        </div>
        <div>
          <h3>Attendance</h3>
          <p>Stay above the 75% line</p>
        </div>
      </div>
      <div className="attendance-ring">
        <strong>
          {overall}
          <span>%</span>
        </strong>
        <small>Overall</small>
      </div>
      <div className="attendance-table">
        {courses.map((c) => {
          const pct = c.held === 0 ? 0 : Math.round((c.attended / c.held) * 100)
          return (
            <div className="attendance-row" key={c.id}>
              <span>{c.course}</span>
              <label>
                Held
                <input type="number" min={0} value={c.held} onChange={(e) => update(c.id, 'held', Number(e.target.value))} />
              </label>
              <label>
                Attended
                <input type="number" min={0} value={c.attended} onChange={(e) => update(c.id, 'attended', Number(e.target.value))} />
              </label>
              <b className={pct < 75 ? 'low' : ''}>{pct}%</b>
              <button className="icon-ghost" onClick={() => removeCourse(c.id)} aria-label={`Remove ${c.course}`}>
                <Trash2 />
              </button>
            </div>
          )
        })}
      </div>
      {formOpen ? (
        <div className="planner-form inline-form">
          <input value={course} onChange={(e) => setCourse(e.target.value)} placeholder="Course name" autoFocus />
          <div className="composer-actions">
            <button className="text-button" onClick={() => setFormOpen(false)}>
              Cancel
            </button>
            <button className="community-ask-btn small" onClick={addCourse}>
              Add
            </button>
          </div>
        </div>
      ) : (
        <button className="utility-link" onClick={() => setFormOpen(true)}>
          <Plus /> Add course
        </button>
      )}
    </section>
  )
}

function ProfessorsSection() {
  const [q, setQ] = useState('')
  const list = useMemo(
    () => professors.filter((p) => `${p.name} ${p.dept}`.toLowerCase().includes(q.toLowerCase())),
    [q],
  )
  return (
    <section>
      <SearchFilter value={q} onChange={setQ} placeholder="Search professors by name or department" />
      <div className="directory-list">
        {list.map((p) => (
          <article className="directory-row" key={p.id}>
            <div className="directory-icon">
              <Users />
            </div>
            <div>
              <strong>{p.name}</strong>
              <span>{p.dept}</span>
              <small>{p.cabin} · {p.email}</small>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

function LabsSection() {
  const [q, setQ] = useState('')
  const list = useMemo(() => labs.filter((l) => `${l.name} ${l.serves}`.toLowerCase().includes(q.toLowerCase())), [q])
  return (
    <section>
      <SearchFilter value={q} onChange={setQ} placeholder="Search labs by name or department" />
      <div className="directory-list">
        {list.map((l) => (
          <article className="directory-row" key={l.id}>
            <div className="directory-icon">
              <Building2 />
            </div>
            <div>
              <strong>{l.name}</strong>
              <span>
                {l.building} · {l.floor} · Room {l.room}
              </span>
              <small>Serves {l.serves}</small>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

function DocumentsSection() {
  const [q, setQ] = useState('')
  const list = useMemo(() => documents.filter((d) => `${d.title} ${d.category}`.toLowerCase().includes(q.toLowerCase())), [q])
  return (
    <section>
      <SearchFilter value={q} onChange={setQ} placeholder="Search regulations, forms, notices" />
      <div className="directory-list">
        {list.map((d) => (
          <article className="directory-row" key={d.id}>
            <div className="directory-icon">
              <FileText />
            </div>
            <div>
              <strong>{d.title}</strong>
              <span>{d.category}</span>
              <small>Updated {d.updated}</small>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

function HelpdeskSection() {
  return (
    <section className="directory-list">
      {helpdeskContacts.map((h) => (
        <article className="directory-row" key={h.id}>
          <div className="directory-icon">
            <HelpCircle />
          </div>
          <div>
            <strong>{h.role}</strong>
            <span>{h.office}</span>
            <small>{h.timings}</small>
          </div>
        </article>
      ))}
    </section>
  )
}

function CouncilSection() {
  return (
    <section className="people-grid">
      {councilMembers.map((c) => (
        <article className="people-card" key={c.id}>
          <div className="network-avatar">{c.name.split(' ').map((n) => n[0]).join('')}</div>
          <strong>{c.name}</strong>
          <span>{c.position}</span>
          <small>{c.branch}</small>
        </article>
      ))}
    </section>
  )
}

function AmenitiesSection() {
  return (
    <section className="people-grid">
      {amenities.map((a) => (
        <article className="people-card" key={a.id}>
          <div className="directory-icon">
            <MapPin />
          </div>
          <strong>{a.name}</strong>
          <span>{a.category}</span>
          <small>{a.location}</small>
        </article>
      ))}
    </section>
  )
}

const sectionComponents: Record<Section, () => React.ReactElement> = {
  gpa: GpaSection,
  attendance: AttendanceSection,
  professors: ProfessorsSection,
  labs: LabsSection,
  documents: DocumentsSection,
  helpdesk: HelpdeskSection,
  council: CouncilSection,
  amenities: AmenitiesSection,
}

export default function UtilitiesPage() {
  const [active, setActive] = useState<Section | null>(null)

  if (active) {
    const SectionComponent = sectionComponents[active]
    const card = hubCards.find((c) => c.id === active)!
    return (
      <div className="view">
        <button className="text-button back-link" onClick={() => setActive(null)}>
          <ArrowLeft /> Back to Utilities
        </button>
        <div className="view-header">
          <div>
            <p className="section-kicker">STUDENT UTILITIES</p>
            <h1>{card.title}</h1>
            <p className="view-sub">{card.subtitle}</p>
          </div>
        </div>
        <SectionComponent />
      </div>
    )
  }

  return (
    <div className="view">
      <div className="view-header">
        <div>
          <p className="section-kicker">STUDENT UTILITIES</p>
          <h1>Useful, when you need it.</h1>
          <p className="view-sub">A directory of everything you need around campus.</p>
        </div>
      </div>
      <div className="utility-hub-grid">
        {hubCards.map((c) => (
          <button className="utility-hub-card" key={c.id} onClick={() => setActive(c.id)}>
            <span className="utility-icon">
              <c.icon />
            </span>
            <strong>{c.title}</strong>
            <span>{c.subtitle}</span>
          </button>
        ))}
        <Link className="utility-hub-card" href="/discover?tab=event">
          <span className="utility-icon">
            <CalendarDays />
          </span>
          <strong>Events</strong>
          <span>See what&apos;s happening on campus</span>
        </Link>
        <Link className="utility-hub-card" href="/discover?tab=club">
          <span className="utility-icon">
            <Users />
          </span>
          <strong>Clubs</strong>
          <span>Browse active student clubs</span>
        </Link>
      </div>
    </div>
  )
}
