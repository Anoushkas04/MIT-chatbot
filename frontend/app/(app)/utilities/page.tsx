'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  ArrowLeft,
  Building2,
  Download,
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
import { gradeOptions } from '@/lib/mock-data'
import { curriculum } from '@/lib/curriculum'
import { getFacultyDirectory, libraryApi, type FacultyMember, type LibraryDocument } from '@/lib/api'
import { useLocalState } from '@/lib/use-local-state'

type Section = 'gpa' | 'professors' | 'labs' | 'documents' | 'helpdesk' | 'amenities'

const hubCards: { id: Section; title: string; subtitle: string; icon: typeof GraduationCap }[] = [
  { id: 'gpa', title: 'GPA Calculator', subtitle: 'GPA, CGPA & aggregate %', icon: GraduationCap },
  { id: 'professors', title: 'Professors', subtitle: 'Official faculty directory', icon: Users },
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

const FACULTY_PAGE = 60
const SCHOOL_SHORT: Record<string, string> = {
  'School of Computer Engineering': 'Computer',
  'School of Electrical Engineering': 'Electrical',
  'School of Mechanical Engineering': 'Mechanical',
  'School of Civil & Chemical Engineering': 'Civil & Chemical',
  'School of Basic Sciences, Humanities & Management': 'Basic Sciences & HM',
}

function ProfessorsSection() {
  const [q, setQ] = useState('')
  const [school, setSchool] = useState<string>('all')
  const [shown, setShown] = useState(FACULTY_PAGE)
  const [faculty, setFaculty] = useState<FacultyMember[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getFacultyDirectory()
      .then((d) => setFaculty(d.faculty))
      .catch((e) => setError(e instanceof Error ? e.message : "Couldn't load the faculty directory."))
  }, [])

  const schools = useMemo(() => [...new Set((faculty ?? []).map((f) => f.department).filter(Boolean))].sort(), [faculty])
  const list = useMemo(() => {
    const term = q.trim().toLowerCase()
    return (faculty ?? []).filter(
      (f) =>
        (school === 'all' || f.department === school) &&
        (!term || `${f.name} ${f.department} ${f.designation} ${f.qualification} ${f.email}`.toLowerCase().includes(term)),
    )
  }, [faculty, q, school])

  useEffect(() => setShown(FACULTY_PAGE), [q, school])

  return (
    <section>
      <SearchFilter value={q} onChange={setQ} placeholder="Search by name, school, designation or email" />
      {schools.length > 0 && (
        <div className="tag-picker directory-filters" role="group" aria-label="Filter by school">
          <button className={school === 'all' ? 'active' : ''} onClick={() => setSchool('all')}>
            All schools
          </button>
          {schools.map((s) => (
            <button key={s} className={school === s ? 'active' : ''} onClick={() => setSchool(s)}>
              {SCHOOL_SHORT[s] ?? s}
            </button>
          ))}
        </div>
      )}
      {error && <p className="community-error">{error}</p>}
      {faculty !== null && (
        <p className="directory-count">
          {list.length} of {faculty.length} faculty · from the official MIT faculty directory
        </p>
      )}
      <div className="directory-list">
        {faculty === null && !error && <p className="view-sub">Loading faculty…</p>}
        {list.slice(0, shown).map((f) => (
          <article className="directory-row" key={f.id}>
            <div className="directory-icon">
              <Users />
            </div>
            <div>
              <strong>{f.name}</strong>
              <span>{[f.designation, f.department].filter(Boolean).join(' · ')}</span>
              {f.qualification && <small>{f.qualification}</small>}
              <small>
                <a href={`mailto:${f.email}`}>{f.email}</a>
                {' · '}
                {f.cabin ? `Cabin: ${f.cabin}` : <span className="muted">Cabin not listed</span>}
              </small>
            </div>
          </article>
        ))}
        {list.length > shown && (
          <button className="text-button directory-more" onClick={() => setShown((n) => n + FACULTY_PAGE)}>
            Show more ({list.length - shown} left)
          </button>
        )}
        {faculty !== null && list.length === 0 && <p className="view-sub">No faculty match.</p>}
      </div>
    </section>
  )
}

// Shown where no official source exists yet, instead of made-up rooms, timings or contacts.
function PendingSource({ what, ask }: { what: string; ask: string }) {
  return (
    <div className="directory-notice">
      <HelpCircle />
      <div>
        <strong>The official {what} isn&apos;t in MITra yet.</strong>
        MITra only shows details from official MIT sources, so nothing is listed here until the MITra team adds the
        official {what}. Until then, {ask}
      </div>
    </div>
  )
}

function LabsSection() {
  return <PendingSource what="labs and facilities directory" ask="ask your department office or course coordinator where a lab is." />
}

function DocumentsSection() {
  const [q, setQ] = useState('')
  const [docs, setDocs] = useState<LibraryDocument[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    libraryApi
      .documents()
      .then((d) => setDocs(d.documents))
      .catch((e) => setError(e instanceof Error ? e.message : "Couldn't load documents."))
  }, [])

  // The same official documents the MITra team manages and the chatbot answers from.
  const list = useMemo(
    () => (docs ?? []).filter((d) => `${d.title} ${d.type}`.toLowerCase().includes(q.toLowerCase())),
    [docs, q],
  )

  async function download(name: string) {
    setError(null)
    try {
      await libraryApi.download(name)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Download failed.')
    }
  }

  return (
    <section>
      <SearchFilter value={q} onChange={setQ} placeholder="Search official documents" />
      {error && <p className="community-error">{error}</p>}
      <div className="directory-list">
        {docs === null && !error && <p className="view-sub">Loading documents…</p>}
        {list.map((d) => (
          <article className="directory-row" key={d.name}>
            <div className="directory-icon">
              <FileText />
            </div>
            <div>
              <strong>{d.title}</strong>
              <span>
                {d.type} · {d.size}
              </span>
              <small>Updated {d.updated}</small>
            </div>
            <button className="icon-ghost directory-download" onClick={() => download(d.name)} aria-label={`Download ${d.title}`} title="Download">
              <Download />
            </button>
          </article>
        ))}
        {docs !== null && list.length === 0 && <p className="view-sub">{q ? 'No documents match.' : 'No documents yet.'}</p>}
      </div>
    </section>
  )
}

function HelpdeskSection() {
  return <PendingSource what="office contact directory" ask="you can reach the Academic Section at ada.mit@manipal.edu or +91 820 2924014 (from MIT notices)." />
}

function AmenitiesSection() {
  return <PendingSource what="campus amenities directory" ask="ask MITra in chat, which answers from the official documents it has." />
}

const sectionComponents: Record<Section, () => React.ReactElement> = {
  gpa: GpaSection,
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
