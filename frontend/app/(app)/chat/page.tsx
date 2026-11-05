'use client'

import { Suspense, useEffect, useRef, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { CalendarDays, ExternalLink, FileText, MessagesSquare, Paperclip, Plus, Send, Sparkles, Users } from 'lucide-react'
import { askMitra, libraryApi, type ChatCitation, type ChatLanguage, type ChatPersona } from '@/lib/api'
import { defaultProfile, type Profile } from '@/lib/mock-data'
import { useLocalState } from '@/lib/use-local-state'

type ChatMessage = {
  id: string
  from: 'ai' | 'user'
  text: string
  time: string
  citations?: ChatCitation[]
  searchedFor?: string | null
}

const languages: { value: ChatLanguage; label: string; placeholder: string }[] = [
  { value: 'en', label: 'English', placeholder: 'Ask about campus, academics, or anything else...' },
  { value: 'hi', label: 'हिन्दी', placeholder: 'कैंपस, पढ़ाई या किसी भी चीज़ के बारे में पूछें...' },
  { value: 'kn', label: 'ಕನ್ನಡ', placeholder: 'ಕ್ಯಾಂಪಸ್, ಓದು ಅಥವಾ ಯಾವುದರ ಬಗ್ಗೆಯೂ ಕೇಳಿ...' },
]

// Who the answer is written for: changes what MITra emphasises (prompts.ROLE_PERSONAS)
const personas: { value: ChatPersona; label: string }[] = [
  { value: 'student', label: 'Me (student)' },
  { value: 'parent', label: 'A parent' },
  { value: 'prospective', label: 'A prospective student' },
]

const kindIcon: Record<ChatCitation['kind'], typeof FileText> = {
  document: FileText,
  calendar: CalendarDays,
  club: ExternalLink,
  faculty: Users,
  community: MessagesSquare,
}

const kindLabel: Record<ChatCitation['kind'], string> = {
  document: 'Official document',
  calendar: 'Academic calendar',
  club: 'Official club page',
  faculty: 'Faculty directory',
  community: 'Student community',
}

/** Answer text with each [E<n>] marker as a button that opens source n. */
function AnswerText({ text, citations, onOpen }: { text: string; citations: ChatCitation[]; onOpen: (c: ChatCitation) => void }) {
  const byIndex = new Map(citations.map((c) => [c.index, c]))
  const parts = text.split(/(\[E\d+\])/g)
  return (
    <>
      {parts.map((part, i) => {
        const n = /^\[E(\d+)\]$/.exec(part)
        const c = n ? byIndex.get(Number(n[1])) : undefined
        if (!n) return <span key={i}>{part}</span>
        if (!c) return null
        return (
          <button key={i} className="cite-marker" onClick={() => onOpen(c)} title={`Open ${c.title}`} aria-label={`Source ${c.index}: ${c.title}`}>
            {c.index}
          </button>
        )
      })}
    </>
  )
}

function seedMessages(): ChatMessage[] {
  return [
    { id: 'm1', from: 'ai', text: "Hey! I'm MITra, your campus companion. What can I help you figure out today?", time: '10:42 AM' },
  ]
}

function ChatInner() {
  const params = useSearchParams()
  const router = useRouter()
  const [openError, setOpenError] = useState<string | null>(null)
  // Answers come back in this language; questions can be typed in any of the three
  const [language, setLanguage] = useLocalState<ChatLanguage>('mitra_chat_language', 'en')
  const [persona, setPersona] = useLocalState<ChatPersona>('mitra_chat_persona', 'student')
  const [profile] = useLocalState<Profile>('mitra_profile', defaultProfile)
  const [messages, setMessages] = useState<ChatMessage[]>(seedMessages)
  const [draft, setDraft] = useState('')
  const [thinking, setThinking] = useState(false)
  const askedRef = useRef(false)
  const idRef = useRef(1)
  // Backend keeps a short per-conversation history keyed by this id
  const sessionIdRef = useRef(crypto.randomUUID())

  function nextId() {
    idRef.current += 1
    return `m${idRef.current}`
  }

  async function ask(text: string) {
    const trimmed = text.trim()
    if (!trimmed) return
    setMessages((prev) => [...prev, { id: nextId(), from: 'user', text: trimmed, time: 'Now' }])
    setThinking(true)
    const conversation = sessionIdRef.current
    let reply: ChatMessage
    try {
      const answer = await askMitra({
        message: trimmed,
        session_id: conversation,
        language,
        role: persona,
        department: profile.branch || null,
        semester: profile.semester || null,
      })
      reply = {
        id: nextId(),
        from: 'ai',
        text: answer.text,
        time: 'Now',
        searchedFor: answer.searched_for,
        // Older servers only send file names; show those as plain documents
        citations:
          answer.citations ??
          answer.sources.map((s, i) => ({ index: i + 1, source: s, title: s, kind: 'document' as const, snippet: '', page_number: null, source_url: null })),
      }
    } catch {
      reply = { id: nextId(), from: 'ai', text: "I couldn't reach MITra's server. Please try again.", time: 'Now' }
    }
    // Drop replies that arrive after "New conversation" was pressed
    if (sessionIdRef.current !== conversation) return
    setMessages((prev) => [...prev, reply])
    setThinking(false)
  }

  useEffect(() => {
    const q = params.get('q')
    if (q && !askedRef.current) {
      askedRef.current = true
      ask(q)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params])

  async function openCitation(c: ChatCitation) {
    setOpenError(null)
    if (c.source_url?.startsWith('http')) {
      window.open(c.source_url, '_blank', 'noopener,noreferrer')
    } else if (c.source_url?.startsWith('/')) {
      router.push(c.source_url)
    } else {
      try {
        await libraryApi.open(c.source, c.page_number)
      } catch (e) {
        setOpenError(e instanceof Error ? e.message : "Couldn't open that source.")
      }
    }
  }

  function send() {
    if (!draft.trim()) return
    ask(draft)
    setDraft('')
  }

  function newConversation() {
    sessionIdRef.current = crypto.randomUUID()
    setMessages(seedMessages())
    setDraft('')
    setThinking(false)
  }

  return (
    <div className="chat-view">
      <div className="chat-head">
        <div>
          <p className="section-kicker">MITRA ASSISTANT</p>
          <h1>Ask MITra</h1>
        </div>
        <div className="chat-head-actions">
          <label className="chat-persona">
            Answer for
            <select value={persona} onChange={(e) => setPersona(e.target.value as ChatPersona)}>
              {personas.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <div className="chat-language" role="group" aria-label="Answer language">
            {languages.map((l) => (
              <button key={l.value} className={language === l.value ? 'active' : ''} onClick={() => setLanguage(l.value)} lang={l.value}>
                {l.label}
              </button>
            ))}
          </div>
          <button className="new-chat" onClick={newConversation}>
            <Plus /> New conversation
          </button>
        </div>
      </div>
      <div className="chat-transcript">
        {messages.map((m) => (
          <div key={m.id} className={`message-row ${m.from}`}>
            <div className={`chat-avatar ${m.from}`}>{m.from === 'ai' ? <Sparkles /> : profile.avatar.emoji}</div>
            <div className="message-body">
              <div className="message-bubble">
                {m.citations?.length ? <AnswerText text={m.text} citations={m.citations} onOpen={openCitation} /> : m.text}
              </div>
              {m.searchedFor && (
                <p className="chat-searched">
                  Searched for: <em>{m.searchedFor}</em>
                </p>
              )}
              {m.citations && m.citations.length > 0 && (
                <div className="chat-sources">
                  <span className="chat-sources-label">Sources</span>
                  {m.citations.map((c) => {
                    const Icon = kindIcon[c.kind] ?? FileText
                    return (
                      <button key={c.index} className="chat-source" onClick={() => openCitation(c)} title={c.snippet || c.title}>
                        <b>{c.index}</b>
                        <Icon />
                        <span>
                          {c.title}
                          {c.page_number ? ` · p. ${c.page_number}` : ''}
                        </span>
                        <small>{kindLabel[c.kind] ?? 'Source'}</small>
                      </button>
                    )
                  })}
                </div>
              )}
              <time>{m.time}</time>
            </div>
          </div>
        ))}
        {thinking && (
          <div className="message-row ai">
            <div className="chat-avatar ai">
              <Sparkles />
            </div>
            <div className="message-body">
              <div className="message-bubble typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>
        )}
      </div>
      {openError && <p className="community-error">{openError}</p>}
      <div className="chat-compose">
        <button className="compose-icon" aria-label="Attach file">
          <Paperclip />
        </button>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.nativeEvent.isComposing) send()
          }}
          placeholder={languages.find((l) => l.value === language)?.placeholder}
        />
        <button className="send-button" onClick={send} aria-label="Send message">
          <Send />
        </button>
      </div>
      <div className="chat-suggestions">
        <span>Try asking</span>
        <button onClick={() => setDraft('How do I calculate my CGPA?')}>How do I calculate my CGPA?</button>
        <button onClick={() => setDraft('What events are happening this week?')}>Events this week</button>
      </div>
    </div>
  )
}

export default function ChatPage() {
  return (
    <Suspense fallback={null}>
      <ChatInner />
    </Suspense>
  )
}
