'use client'

import { useMemo, useState } from 'react'
import {
  ArrowLeft,
  BookOpen,
  Building2,
  ChevronDown,
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
  defaultAttendanceCourses,
  documents,
  gradeOptions,
  helpdeskContacts,
  labs,
  professors,
  type AttendanceCourse,
} from '@/lib/mock-data'
import { curriculum } from '@/lib/curriculum'
import { useLocalState } from '@/lib/use-local-state'

type Section = 'gpa' | 'attendance' | 'professors' | 'labs' | 'documents' | 'helpdesk' | 'amenities'

const hubCards: { id: Section; title: string; subtitle: string; icon: typeof GraduationCap }[] = [
  { id: 'gpa', title: 'GPA Calculator', subtitle: 'GPA, CGPA & aggregate %', icon: GraduationCap },
  { id: 'attendance', title: 'Attendance Calculator', subtitle: 'Stay above the 75% line', icon: BookOpen },
  { id: 'professors', title: 'Professors', subtitle: 'Find your professors on campus', icon: Users },
  { id: 'labs', title: 'Labs', subtitle: 'Locate department labs', icon: Building2 },
  { id: 'documents', title: 'Documents', subtitle: 'Regulations, forms & notices', icon: FileText },
  { id: 'helpdesk', title: 'Academic Helpdesk', subtitle: 'Who to contact, and when', icon: HelpCircle },
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

const ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']
const BRANCHES: { label: string; value: string }[] = [
  { label: 'CSE', value: 'CS' },
  { label: 'AIML', value: 'AIML' },
  { label: 'CCE', value: 'CCE' },
  { label: 'IT', value: 'IT' },
  { label: 'DSE', value: 'DSE' },
  { label: 'MNC', value: 'MNC' },
  { label: 'CSFT', value: 'CSFT' },
  { label: 'ECE', value: 'ECE' },
  { label: 'VLSI', value: 'VLSI' },
  { label: 'ENI', value: 'ENI' },
  { label: 'EEE', value: 'EEE' },
  { label: 'CPS', value: 'CPS' },
  { label: 'BioMed', value: 'BioMed' },
  { label: 'MechX', value: 'MechX' },
  { label: 'Mech', value: 'Mech' },
  { label: 'Aero', value: 'Aero' },
  { label: 'Auto', value: 'Auto' },
  { label: 'Industrial', value: 'Industrial' },
  { label: 'Civil', value: 'Civil' },
  { label: 'BioTech', value: 'BioTech' },
  { label: 'Chem', value: 'Chem' },
]

type GpaSelection = {
  semester: number | null
  cycle: 'PHY' | 'CHM' | null
  stream: 'CS' | 'NONCS' | null
  branch: string | null
  honors: boolean
  minors: boolean
  // Grades are kept per subject group so switching semester/branch doesn't lose them.
  grades: Record<string, Record<string, string>>
}

const emptySelection: GpaSelection = { semester: null, cycle: null, stream: null, branch: null, honors: false, minors: false, grades: {} }

function subjectGroup(s: GpaSelection): string | null {
  if (!s.semester) return null
  if (s.semester <= 2) return s.cycle && s.stream ? `${s.semester}-${s.stream}-${s.cycle}` : null
  return s.branch ? `${s.semester}-${s.branch}` : null
}

function ChoiceRow<T extends string | number>({
  label,
  options,
  value,
  onChange,
}: {
  label: string
  options: { label: string; value: T }[]
  value: T | null
  onChange: (v: T) => void
}) {
  return (
    <div className="gpa-step">
      <span className="gpa-step-label">{label}</span>
      <div className="tag-picker">
        {options.map((o) => (
          <button key={String(o.value)} className={value === o.value ? 'active' : ''} onClick={() => onChange(o.value)}>
            {o.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function GpaSection() {
  const [sel, setSel] = useLocalState<GpaSelection>('mitra_gpa_calc', emptySelection)
  const [previous, setPrevious] = useLocalState<{ cgpa: string; credits: string }>('mitra_gpa_previous', { cgpa: '', credits: '' })
  const [result, setResult] = useState<{ gpa: number; points: number; credits: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [guideOpen, setGuideOpen] = useState(false)

  const group = subjectGroup(sel)
  const groupGrades = (group && sel.grades[group]) || {}
  // Honors subjects only with the Honors option (sem 8); stand-alone minor courses only with
  // the Minor option (sem 7). Program electives that double as minors always show.
  const subjects = group
    ? Object.entries(curriculum[group] ?? {}).filter(
        ([name]) => !(!sel.honors && name.includes('Honors')) && !(!sel.minors && name.includes('Minor') && !name.includes('Program')),
      )
    : []

  function update(patch: Partial<GpaSelection>) {
    setSel((prev) => ({ ...prev, ...patch }))
    setResult(null)
    setError(null)
  }

  function setGrade(subject: string, grade: string) {
    if (!group) return
    setSel((prev) => ({ ...prev, grades: { ...prev.grades, [group]: { ...(prev.grades[group] ?? {}), [subject]: grade } } }))
    setResult(null)
    setError(null)
  }

  // GPA = Σ(Grade Points × Credits) / Σ(Credits), over subjects that have a grade (Regulations 4.8.2).
  function calculate() {
    let points = 0
    let credits = 0
    for (const [name, cr] of subjects) {
      const g = gradeOptions.find((o) => o.grade === groupGrades[name])
      if (!g) continue
      points += g.value * cr
      credits += cr
    }
    if (credits === 0) {
      setError('Please select grades for at least one subject!')
      return
    }
    setResult({ gpa: Number((points / credits).toFixed(2)), points, credits })
  }

  // CGPA weights every graded course to date (4.8.3); earlier semesters enter as CGPA × credits.
  const prevCgpa = Number(previous.cgpa)
  const prevCredits = Number(previous.credits)
  const prevValid = previous.cgpa !== '' && previous.credits !== '' && prevCgpa >= 0 && prevCgpa <= 10 && prevCredits > 0
  const cgpa = result
    ? (result.points + (prevValid ? prevCgpa * prevCredits : 0)) / (result.credits + (prevValid ? prevCredits : 0))
    : null

  return (
    <section className="utility-card gpa-card">
      <div className="utility-heading">
        <div className="utility-icon">
          <GraduationCap />
        </div>
        <div>
          <h3>GPA calculator</h3>
          <p>Select your semester, stream, and grades to calculate your GPA.</p>
        </div>
      </div>

      <button className="gpa-guide-toggle" onClick={() => setGuideOpen((v) => !v)} aria-expanded={guideOpen}>
        How does grading work? <ChevronDown className={guideOpen ? 'open' : ''} />
      </button>
      {guideOpen && (
        <div className="gpa-guide">
          <strong>Grade point scale</strong>
          <p>{gradeOptions.map((g) => `${g.grade}: ${g.value}`).join(' · ')}</p>
          <strong>GPA calculation</strong>
          <p className="gpa-formula">GPA = Σ(Grade Points × Credits) / Σ(Credits)</p>
          <p>Only subjects you&apos;ve picked a grade for are counted. An F counts with its credits.</p>
        </div>
      )}

      <ChoiceRow
        label="Select your semester"
        options={ROMAN.map((r, i) => ({ label: r, value: i + 1 }))}
        value={sel.semester}
        onChange={(semester) => update({ semester })}
      />
      {sel.semester !== null && sel.semester <= 2 && (
        <>
          <ChoiceRow
            label="Cycle"
            options={[
              { label: 'Physics Cycle', value: 'PHY' as const },
              { label: 'Chemistry Cycle', value: 'CHM' as const },
            ]}
            value={sel.cycle}
            onChange={(cycle) => update({ cycle })}
          />
          <ChoiceRow
            label="Stream"
            options={[
              { label: 'CS Stream', value: 'CS' as const },
              { label: 'Non-CS Stream', value: 'NONCS' as const },
            ]}
            value={sel.stream}
            onChange={(stream) => update({ stream })}
          />
        </>
      )}
      {sel.semester !== null && sel.semester > 2 && (
        <ChoiceRow label="Branch" options={BRANCHES} value={sel.branch} onChange={(branch) => update({ branch })} />
      )}
      {sel.semester === 8 && (
        <label className="report-check gpa-option">
          <input type="checkbox" checked={sel.honors} onChange={(e) => update({ honors: e.target.checked })} />
          B.Tech Honors Program
        </label>
      )}
      {sel.semester === 7 && (
        <label className="report-check gpa-option">
          <input type="checkbox" checked={sel.minors} onChange={(e) => update({ minors: e.target.checked })} />
          Include Minor Course
        </label>
      )}

      {subjects.length > 0 && (
        <>
          <div className="gpa-table" role="table">
            <div className="gpa-table-head" role="row">
              <span>Subject</span>
              <span>Credits</span>
              <span>Grade (/A+)</span>
            </div>
            {subjects.map(([name, cr]) => (
              <div key={name} className="gpa-table-row" role="row">
                <span>{name}</span>
                <span>{cr}</span>
                <select
                  className="grade-select"
                  value={groupGrades[name] ?? ''}
                  onChange={(e) => setGrade(name, e.target.value)}
                  aria-label={`Grade for ${name}`}
                >
                  <option value="" disabled>
                    Grade
                  </option>
                  {gradeOptions.map((g) => (
                    <option key={g.grade} value={g.grade}>
                      {g.grade}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          <button className="community-ask-btn gpa-calc-btn" onClick={calculate}>
            Calculate GPA
          </button>
          {error && <p className="cgpa-error">{error}</p>}
          {result && (
            <div className="gpa-score">
              <strong>{result.gpa.toFixed(2)}</strong>
              <span>Your calculated GPA · {result.credits} credits</span>
            </div>
          )}
        </>
      )}

      <div className="cgpa-block">
        <h4>CGPA</h4>
        <p>Add your CGPA and credits from earlier semesters to include this semester.</p>
        <div className="cgpa-inputs">
          <label>
            Previous CGPA
            <input
              type="number"
              inputMode="decimal"
              min={0}
              max={10}
              step={0.01}
              value={previous.cgpa}
              onChange={(e) => setPrevious((p) => ({ ...p, cgpa: e.target.value }))}
              placeholder="e.g. 8.42"
            />
          </label>
          <label>
            Credits completed
            <input
              type="number"
              inputMode="numeric"
              min={0}
              step={1}
              value={previous.credits}
              onChange={(e) => setPrevious((p) => ({ ...p, credits: e.target.value }))}
              placeholder="e.g. 80"
            />
          </label>
        </div>
        {(previous.cgpa !== '' || previous.credits !== '') && !prevValid && (
          <p className="cgpa-error">Enter a CGPA between 0 and 10 and the credits it covers.</p>
        )}
        <div className="cgpa-results">
          <div>
            <strong>{cgpa === null ? '—' : cgpa.toFixed(2)}</strong>
            <span>{prevValid ? 'cumulative CGPA' : 'CGPA (this semester only)'}</span>
          </div>
          <div>
            {/* Senate guideline (4.8.3.1): aggregate % = CGPA × 10 */}
            <strong>{cgpa === null ? '—' : `${(cgpa * 10).toFixed(2)}%`}</strong>
            <span>aggregate marks</span>
          </div>
        </div>
        {cgpa === null && <p className="cgpa-hint">Calculate your GPA above to see your CGPA.</p>}
      </div>
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
      </div>
    </div>
  )
}
