'use client'

import { useId, useState } from 'react'
import { AlertCircle, BookOpen, Plus, RotateCcw, Send, Sparkles, Users } from 'lucide-react'
import { sendChatMessage, type ChatCitation } from '@/lib/api'

type Message = { id: string; from: 'ai' | 'user'; text: string; citations?: ChatCitation[]; confidence?: string; followups?: string[]; provider?: string }
const welcome: Message = { id: 'welcome', from: 'ai', text: 'Hi! I’m MITra. Ask a campus question and I’ll answer from the sources currently indexed by CampusOS.' }

export function ChatView() {
  const generatedSessionId = useId().replace(/:/g, '-')
  const [messages, setMessages] = useState<Message[]>([welcome])
  const [draft, setDraft] = useState('')
  const [sessionId, setSessionId] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const [lastQuestion, setLastQuestion] = useState('')
  const [selectedCitation, setSelectedCitation] = useState<ChatCitation | null>(null)

  const submit = async (question = draft) => {
    const text = question.trim()
    if (!text || pending) return
    const activeSession = sessionId || `guest-${generatedSessionId}`
    if (!sessionId) setSessionId(activeSession)
    setMessages(current => [...current, { id: `user-${current.length}`, from: 'user', text }])
    setDraft(''); setError(''); setLastQuestion(text); setPending(true)
    try {
      const response = await sendChatMessage({ message: text, session_id: activeSession, role: 'student', language: 'en' })
      setMessages(current => [...current, {
        id: `ai-${current.length}`, from: 'ai', text: response.text, citations: response.citations,
        confidence: response.confidence, followups: response.followups, provider: response.provider,
      }])
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'MITra could not answer right now.')
    } finally { setPending(false) }
  }

  const reset = () => { setMessages([welcome]); setSessionId(''); setDraft(''); setError(''); setSelectedCitation(null) }

  return <div className="chat-view">
    <div className="chat-head"><div><p className="section-kicker">MITRA ASSISTANT · LIVE RAG</p><h1>Ask MITra</h1></div><button className="new-chat" onClick={reset}><Plus /> New conversation</button></div>
    <div className="chat-transcript" aria-live="polite">
      {messages.map(message => <div key={message.id} className={`message-row ${message.from}`}>
        <div className={`chat-avatar ${message.from}`}>{message.from === 'ai' ? <Sparkles /> : 'G'}</div>
        <div className="message-body"><div className="message-bubble">{message.text}</div>
          {message.confidence && <small className="answer-meta">Confidence: {message.confidence}{message.provider ? ` · ${message.provider}` : ''}</small>}
          {!!message.citations?.length && <div className="citation-row">{message.citations.map((citation, index) => <button key={`${citation.source}-${index}`} onClick={() => setSelectedCitation(citation)}><BookOpen /> Source {index + 1}</button>)}</div>}
          {!!message.followups?.length && <div className="chat-suggestions"><span>Follow up</span>{message.followups.map(item => <button key={item} onClick={() => void submit(item)}>{item}</button>)}</div>}
        </div>
      </div>)}
      {pending && <div className="message-row ai"><div className="chat-avatar ai"><Sparkles /></div><div className="message-body"><div className="message-bubble loading-answer">Searching indexed sources…</div></div></div>}
      {error && <div className="inline-error"><AlertCircle /><span>{error}</span><button onClick={() => void submit(lastQuestion)}><RotateCcw /> Retry</button></div>}
    </div>
    <div className="chat-compose"><input value={draft} onChange={event => setDraft(event.target.value)} onKeyDown={event => { if (event.key === 'Enter' && !event.nativeEvent.isComposing) void submit() }} placeholder="Ask a question grounded in campus sources…" disabled={pending} /><button className="send-button" onClick={() => void submit()} disabled={pending || !draft.trim()}><Send /></button></div>
    <div className="community-handoff"><Users /><span>Not enough official evidence? MITra will say so clearly. Community posting remains read-only in guest mode.</span></div>
    {selectedCitation && <aside className="citation-drawer"><button onClick={() => setSelectedCitation(null)}>Close</button><p className="section-kicker">RETRIEVED SOURCE</p><h3>{selectedCitation.source}{selectedCitation.page_number ? ` · page ${selectedCitation.page_number}` : ''}</h3><p>{selectedCitation.snippet}</p><small>Retrieval: {selectedCitation.retrieval_method || 'indexed'} · score {selectedCitation.score.toFixed(2)}</small>{selectedCitation.source_url && <p><a href={selectedCitation.source_url} target="_blank" rel="noreferrer">Open cited page</a></p>}</aside>}
  </div>
}
