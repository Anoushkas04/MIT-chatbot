'use client'

import { useState } from 'react'
import { Check, Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  ACADEMIC_YEAR_LABEL,
  academicEventsBetween,
  academicEventsOn,
  academicKindLabels,
  academicKindPriority,
  formatAcademicRange,
  type AcademicEvent,
  type AcademicEventKind,
} from '@/lib/academic-calendar'
import { defaultPlannerTasks, type PlannerTask } from '@/lib/mock-data'
import { useLocalState } from '@/lib/use-local-state'

const weekLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
const categories = ['Academic', 'Event', 'Important', 'Personal']
const academicFilters: Array<AcademicEventKind | 'all'> = ['all', 'exam', 'holiday', 'fest', 'registration', 'academic']

function topKind(events: AcademicEvent[]): AcademicEventKind | null {
  return academicKindPriority.find((k) => events.some((e) => e.kind === k)) ?? null
}

function AcademicRow({ event }: { event: AcademicEvent }) {
  return (
    <div className="deadline academic-row">
      <time>{formatAcademicRange(event)}</time>
      <div>
        <strong>{event.title}</strong>
        {event.note && <span>{event.note}</span>}
      </div>
      <span className={`academic-pill ac-${event.kind}`}>{academicKindLabels[event.kind]}</span>
    </div>
  )
}

function pad(n: number) {
  return n.toString().padStart(2, '0')
}

function toIso(year: number, month: number, day: number) {
  return `${year}-${pad(month + 1)}-${pad(day)}`
}

function mondayFirstIndex(date: Date) {
  const wd = date.getDay()
  return wd === 0 ? 6 : wd - 1
}

export default function PlannerPage() {
  const [tasks, setTasks] = useLocalState<PlannerTask[]>('mitra_planner_tasks', defaultPlannerTasks)
  const today = new Date()
  const todayIso = today.toISOString().slice(0, 10)
  const [viewMonth, setViewMonth] = useState(new Date(today.getFullYear(), today.getMonth(), 1))
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [date, setDate] = useState(todayIso)
  const [category, setCategory] = useState(categories[0])
  const [academicFilter, setAcademicFilter] = useState<AcademicEventKind | 'all'>('all')

  const year = viewMonth.getFullYear()
  const month = viewMonth.getMonth()
  const totalDays = new Date(year, month + 1, 0).getDate()
  const leadingBlanks = mondayFirstIndex(new Date(year, month, 1))
  const monthLabel = viewMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

  const taskDates = new Set(tasks.map((t) => t.date))
  const monthAcademic = academicEventsBetween(toIso(year, month, 1), toIso(year, month, totalDays))
  const filteredMonthAcademic =
    academicFilter === 'all' ? monthAcademic : monthAcademic.filter((e) => e.kind === academicFilter)
  const selectedAcademic = selectedDate ? academicEventsOn(selectedDate) : []

  function changeMonth(delta: number) {
    setViewMonth(new Date(year, month + delta, 1))
  }

  function addTask() {
    if (!title.trim()) return
    const task: PlannerTask = { id: `t-${Date.now()}`, date, title: title.trim(), category, done: false }
    setTasks((prev) => [...prev, task])
    setTitle('')
    setFormOpen(false)
  }

  function toggleDone(id: string) {
    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, done: !t.done } : t)))
  }

  function deleteTask(id: string) {
    setTasks((prev) => prev.filter((t) => t.id !== id))
  }

  const visibleTasks = (selectedDate ? tasks.filter((t) => t.date === selectedDate) : tasks)
    .slice()
    .sort((a, b) => a.date.localeCompare(b.date))

  return (
    <div className="view">
      <div className="view-header">
        <div>
          <p className="section-kicker">YOUR PLANNER</p>
          <h1>Keep moving forward.</h1>
          <p className="view-sub">A calm view of what&apos;s coming up next.</p>
        </div>
        <Button
          onClick={() => {
            setDate(selectedDate ?? todayIso)
            setFormOpen((v) => !v)
          }}
        >
          <Plus data-icon="inline-start" /> Add task
        </Button>
      </div>

      {formOpen && (
        <div className="planner-form">
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Task title" autoFocus />
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <div className="composer-actions">
            <button className="text-button" onClick={() => setFormOpen(false)}>
              Cancel
            </button>
            <button className="community-ask-btn small" onClick={addTask}>
              Save task
            </button>
          </div>
        </div>
      )}

      <div className="planner-layout">
        <section className="planner-card">
          <div className="planner-month">
            <button onClick={() => changeMonth(-1)} aria-label="Previous month">
              ‹
            </button>
            <h3>{monthLabel}</h3>
            <button onClick={() => changeMonth(1)} aria-label="Next month">
              ›
            </button>
          </div>
          <div className="week-days">
            {weekLabels.map((d, i) => (
              <span key={i}>{d}</span>
            ))}
          </div>
          <div className="calendar-grid">
            {Array.from({ length: leadingBlanks }, (_, i) => <span key={`b${i}`} />)}
            {Array.from({ length: totalDays }, (_, i) => {
              const day = i + 1
              const iso = toIso(year, month, day)
              const dayAcademic = academicEventsOn(iso)
              const kind = topKind(dayAcademic.filter((e) => !e.listOnly))
              const classes = [
                iso === todayIso ? 'today' : '',
                taskDates.has(iso) ? 'has-event' : '',
                iso === selectedDate ? 'selected' : '',
                kind ? `ac-day ac-${kind}` : '',
              ]
                .filter(Boolean)
                .join(' ')
              return (
                <button
                  key={iso}
                  className={classes}
                  title={dayAcademic.map((e) => e.title).join(' · ') || undefined}
                  onClick={() => setSelectedDate(iso === selectedDate ? null : iso)}
                >
                  {day}
                </button>
              )
            })}
          </div>
          <div className="academic-legend">
            {academicKindPriority.map((k) => (
              <span key={k}>
                <i className={`ac-${k}`} /> {academicKindLabels[k]}
              </span>
            ))}
          </div>
        </section>
        <section className="deadline-card">
          <div className="card-heading">
            <div>
              <p className="section-kicker">{selectedDate ? 'SELECTED DAY' : 'UP NEXT'}</p>
              <h3>Deadlines &amp; reminders</h3>
            </div>
            {selectedDate && (
              <button onClick={() => setSelectedDate(null)}>
                Show all
              </button>
            )}
          </div>
          {selectedAcademic.map((e) => (
            <AcademicRow key={e.id} event={e} />
          ))}
          {visibleTasks.map((t) => (
            <div className={`deadline ${t.done ? 'done' : ''}`} key={t.id}>
              <time>
                {new Date(t.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </time>
              <div>
                <strong>{t.title}</strong>
                <span>{t.category}</span>
              </div>
              <button className="icon-ghost" onClick={() => toggleDone(t.id)} aria-label={t.done ? 'Mark incomplete' : 'Mark complete'}>
                <Check />
              </button>
              <button className="icon-ghost" onClick={() => deleteTask(t.id)} aria-label="Delete task">
                <Trash2 />
              </button>
            </div>
          ))}
          {visibleTasks.length === 0 && selectedAcademic.length === 0 && (
            <p className="view-sub">Nothing here. Add a task to get started.</p>
          )}
        </section>
        <section className="deadline-card academic-card">
          <div className="card-heading">
            <div>
              <p className="section-kicker">ACADEMIC CALENDAR {ACADEMIC_YEAR_LABEL}</p>
              <h3>{monthLabel}</h3>
            </div>
          </div>
          <div className="academic-filters">
            {academicFilters.map((f) => (
              <button key={f} className={f === academicFilter ? 'active' : ''} onClick={() => setAcademicFilter(f)}>
                {f === 'all' ? 'All' : academicKindLabels[f]}
              </button>
            ))}
          </div>
          {filteredMonthAcademic.map((e) => (
            <AcademicRow key={e.id} event={e} />
          ))}
          {filteredMonthAcademic.length === 0 && (
            <p className="view-sub">No {academicFilter === 'all' ? '' : `${academicKindLabels[academicFilter].toLowerCase()} `}dates this month.</p>
          )}
        </section>
      </div>
    </div>
  )
}
