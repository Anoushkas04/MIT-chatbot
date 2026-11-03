'use client'

import { Suspense, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { FileText, Paperclip, Plus, Send, Sparkles } from 'lucide-react'
import { askMitra } from '@/lib/api'
import { defaultProfile, type Profile } from '@/lib/mock-data'
import { useLocalState } from '@/lib/use-local-state'

type ChatMessage = {
  id: string
  from: 'ai' | 'user'
  text: string
  time: string
  source?: { title: string; office: string }
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
      const firstSource = answer.sources[0]
      reply = {
        id: nextId(),
        from: 'ai',
        text: answer.text,
        time: 'Now',
        source: firstSource
          ? {
              title: firstSource,
              office: answer.confidence_type === 'community_grounded' ? 'Student community' : 'Official document',
            }
          : undefined,
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
              {m.source && (
                <div className="citation">
                  <FileText /> Source: {m.source.title} · {m.source.office}
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
