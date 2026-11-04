'use client'

import { useId, useState } from 'react'
import { X } from 'lucide-react'
import type { ProfileEntry } from '@/lib/api'

/** Editable list of clubs or student projects, each with an optional role. */
export function ProfileEntriesEditor({
  entries,
  onChange,
  suggestions = [],
  namePlaceholder,
  rolePlaceholder,
}: {
  entries: ProfileEntry[]
  onChange: (entries: ProfileEntry[]) => void
  suggestions?: string[]
  namePlaceholder: string
  rolePlaceholder: string
}) {
  const listId = useId()
  const [name, setName] = useState('')
  const [role, setRole] = useState('')

  function add() {
    const clean = name.trim()
    if (!clean) return
    if (!entries.some((e) => e.name.toLowerCase() === clean.toLowerCase())) {
      onChange([...entries, { name: clean, role: role.trim() }])
    }
    setName('')
    setRole('')
  }

  function onEnter(e: React.KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault()
      add()
    }
  }

  return (
    <div className="entries-editor">
      {entries.length > 0 && (
        <ul className="entries-list">
          {entries.map((e) => (
            <li key={e.name}>
              <span>
                <strong>{e.name}</strong>
                {e.role && <em>{e.role}</em>}
              </span>
              <button
                className="icon-ghost"
                onClick={() => onChange(entries.filter((x) => x.name !== e.name))}
                aria-label={`Remove ${e.name}`}
              >
                <X />
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="entries-add-row">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={onEnter}
          placeholder={namePlaceholder}
          list={suggestions.length > 0 ? listId : undefined}
          maxLength={80}
        />
        <input value={role} onChange={(e) => setRole(e.target.value)} onKeyDown={onEnter} placeholder={rolePlaceholder} maxLength={60} />
        <button className="text-button" onClick={add}>
          Add
        </button>
      </div>
      {suggestions.length > 0 && (
        <datalist id={listId}>
          {suggestions.map((s) => (
            <option key={s} value={s} />
          ))}
        </datalist>
      )}
    </div>
  )
}
