'use client'

import { Suspense, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { ExternalLink, FileText, Paperclip, Plus, Send, Sparkles, X } from 'lucide-react'
import { API_BASE, askMitra, type CitationDetail } from '@/lib/api'
import { defaultProfile, type Profile } from '@/lib/mock-data'
import { useLocalState } from '@/lib/use-local-state'

type ChatMessage = {
  id: string
  from: 'ai' | 'user'
  text: string
  time: string
  citations?: CitationDetail[]
}

function CitationModal({ citation, onClose }: { citation: CitationDetail; onClose: () => void }) {
  const pageUrl = citation.source_url ? `${API_BASE}${citation.source_url}` : null
  return (
    <div className="citation-modal-overlay" onClick={onClose}>
      <div className="citation-modal" onClick={(e) => e.stopPropagation()}>
        <div className="citation-modal-head">
          <div>
            <strong>{citation.source}</strong>
            {citation.page_number != null && <span>Page {citation.page_number}</span>}
          </div>
          <button className="icon-ghost" onClick={onClose} aria-label="Close">
            <X />
          </button>
        </div>
        {pageUrl ? (
          <img className="citation-modal-page" src={pageUrl} alt={`${citation.source}, page ${citation.page_number}`} />
        ) : (
          <p className="citation-modal-snippet">{citation.snippet}</p>
        )}
        {pageUrl && (
          <a className="citation-modal-open" href={pageUrl} target="_blank" rel="noreferrer">
            Open full size <ExternalLink />
          </a>
        )}
      </div>
    </div>
  )
}

function seedMessages(): ChatMessage[] {
  return [
    { id: 'm1', from: 'ai', text: "Hey! I'm MITra, your campus companion. What can I help you figure out today?", time: '10:42 AM' },
  ]
}

function ChatInner() {
  const params = useSearchParams()
  const [profile] = useLocalState<Profile>('mitra_profile', defaultProfile)
  const [messages, setMessages] = useState<ChatMessage[]>(seedMessages)
  const [draft, setDraft] = useState('')
  const [thinking, setThinking] = useState(false)
  const [viewingCitation, setViewingCitation] = useState<CitationDetail | null>(null)
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
        department: profile.branch || null,
        semester: profile.semester || null,
      })
      reply = {
        id: nextId(),
        from: 'ai',
        text: answer.text,
        time: 'Now',
        citations: answer.citations,
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
        <button className="new-chat" onClick={newConversation}>
          <Plus /> New conversation
        </button>
      </div>
      <div className="chat-transcript">
        {messages.map((m) => (
          <div key={m.id} className={`message-row ${m.from}`}>
            <div className={`chat-avatar ${m.from}`}>{m.from === 'ai' ? <Sparkles /> : profile.avatar.emoji}</div>
            <div className="message-body">
              <div className="message-bubble">{m.text}</div>
              {m.citations && m.citations.length > 0 && (
                <div className="citation-list">
                  {m.citations.map((c, i) => (
                    <button key={i} className="citation-chip" onClick={() => setViewingCitation(c)}>
                      <FileText />
                      {c.source}
                      {c.page_number != null && <span>· p.{c.page_number}</span>}
                    </button>
                  ))}
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
          placeholder="Ask about campus, academics, or anything else..."
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
      {viewingCitation && <CitationModal citation={viewingCitation} onClose={() => setViewingCitation(null)} />}
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
