'use client'

import { useState } from 'react'
import { ArrowBigDown, ArrowBigUp, BadgeCheck, MessageSquare, Pencil, Plus, Trash2 } from 'lucide-react'
import {
  communityQuestions as seedQuestions,
  defaultProfile,
  type CommunityAnswer,
  type CommunityQuestion,
  type CommunityReply,
  type Profile,
} from '@/lib/mock-data'
import { useLocalState } from '@/lib/use-local-state'

const VERIFIED_THRESHOLD = 10
const tagOptions = ['Academics', 'Attendance', 'Exams', 'Hostel', 'Campus Life', 'Clubs', 'Opportunities', 'Registration']

type SortMode = 'top' | 'new' | 'unanswered'
type Votes = Record<string, 1 | -1>

function applyDelta(list: CommunityQuestion[], id: string, delta: number): CommunityQuestion[] {
  return list.map((q) => {
    if (q.id === id) return { ...q, votes: q.votes + delta }
    return {
      ...q,
      answers: q.answers.map((a) => {
        if (a.id === id) return { ...a, votes: a.votes + delta }
        return { ...a, replies: a.replies.map((r) => (r.id === id ? { ...r, votes: r.votes + delta } : r)) }
      }),
    }
  })
}

function VoteControl({ id, votes, myVotes, onVote }: { id: string; votes: number; myVotes: Votes; onVote: (id: string, dir: 1 | -1) => void }) {
  const mine = myVotes[id]
  return (
    <div className="vote-control">
      <button className={mine === 1 ? 'active-up' : ''} onClick={() => onVote(id, 1)} aria-label="Upvote">
        <ArrowBigUp />
      </button>
      <span>{votes}</span>
      <button className={mine === -1 ? 'active-down' : ''} onClick={() => onVote(id, -1)} aria-label="Downvote">
        <ArrowBigDown />
      </button>
    </div>
  )
}

function ReplyBox({ placeholder, onSubmit, onCancel }: { placeholder: string; onSubmit: (text: string) => void; onCancel: () => void }) {
  const [text, setText] = useState('')
  return (
    <div className="reply-box">
      <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder={placeholder} autoFocus />
      <div className="composer-actions">
        <button className="text-button" onClick={onCancel}>
          Cancel
        </button>
        <button
          className="community-ask-btn small"
          onClick={() => {
            if (!text.trim()) return
            onSubmit(text)
            setText('')
          }}
        >
          Post
        </button>
      </div>
    </div>
  )
}

function ReplyRow({ reply, myVotes, onVote }: { reply: CommunityReply; myVotes: Votes; onVote: (id: string, dir: 1 | -1) => void }) {
  return (
    <div className="reply-row">
      <span className="comment-avatar small">{reply.initials}</span>
      <div>
        <div className="community-meta">
          <strong>{reply.author}</strong>
          <time>{reply.time}</time>
        </div>
        <p>{reply.body}</p>
        <VoteControl id={reply.id} votes={reply.votes} myVotes={myVotes} onVote={onVote} />
      </div>
    </div>
  )
}

function AnswerRow({
  questionId,
  answer,
  myVotes,
  onVote,
  onAddReply,
}: {
  questionId: string
  answer: CommunityAnswer
  myVotes: Votes
  onVote: (id: string, dir: 1 | -1) => void
  onAddReply: (questionId: string, answerId: string, body: string) => void
}) {
  const [replyOpen, setReplyOpen] = useState(false)
  const verified = answer.votes >= VERIFIED_THRESHOLD
  return (
    <div className="answer-row">
      <span className="comment-avatar">{answer.initials}</span>
      <div className="answer-body">
        <div className="community-meta">
          <strong>{answer.author}</strong>
          <time>{answer.time}</time>
          {verified && (
            <span className="verified-tag">
              <BadgeCheck /> Community verified
            </span>
          )}
        </div>
        <p>{answer.body}</p>
        <div className="comment-actions">
          <VoteControl id={answer.id} votes={answer.votes} myVotes={myVotes} onVote={onVote} />
          <button onClick={() => setReplyOpen((v) => !v)}>
            <MessageSquare /> Reply
          </button>
        </div>
        {replyOpen && (
          <ReplyBox
            placeholder={`Reply to ${answer.author}...`}
            onCancel={() => setReplyOpen(false)}
            onSubmit={(text) => {
              onAddReply(questionId, answer.id, text)
              setReplyOpen(false)
            }}
          />
        )}
        {answer.replies.length > 0 && (
          <div className="reply-list">
            {answer.replies.map((r) => (
              <ReplyRow key={r.id} reply={r} myVotes={myVotes} onVote={onVote} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function QuestionCard({
  question,
  isOwn,
  myVotes,
  onVote,
  onAddAnswer,
  onAddReply,
  onEdit,
  onDelete,
}: {
  question: CommunityQuestion
  isOwn: boolean
  myVotes: Votes
  onVote: (id: string, dir: 1 | -1) => void
  onAddAnswer: (questionId: string, body: string) => void
  onAddReply: (questionId: string, answerId: string, body: string) => void
  onEdit: (questionId: string, title: string, body: string) => void
  onDelete: (questionId: string) => void
}) {
  const [replyOpen, setReplyOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(question.title)
  const [editBody, setEditBody] = useState(question.body)

  function handleSaveEdit() {
    if (!editTitle.trim() || !editBody.trim()) return
    onEdit(question.id, editTitle.trim(), editBody.trim())
    setEditing(false)
  }

  function handleCancelEdit() {
    setEditTitle(question.title)
    setEditBody(question.body)
    setEditing(false)
  }

  return (
    <article className="community-card">
      <VoteControl id={question.id} votes={question.votes} myVotes={myVotes} onVote={onVote} />
      <div className="community-body">
        <div className="community-meta">
          <span className="comment-avatar">{question.initials}</span>
          <strong>{question.author}</strong>
          <time>{question.time}</time>
          {question.edited && <span className="edited-tag">edited</span>}
          {isOwn && !editing && (
            <div className="own-post-actions">
              <button className="icon-action" onClick={() => setEditing(true)} aria-label="Edit post" title="Edit">
                <Pencil size={14} />
              </button>
              <button className="icon-action danger" onClick={() => onDelete(question.id)} aria-label="Delete post" title="Delete">
                <Trash2 size={14} />
              </button>
            </div>
          )}
        </div>

        {editing ? (
          <div className="community-composer inline-edit">
            <input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} placeholder="Question title" />
            <textarea value={editBody} onChange={(e) => setEditBody(e.target.value)} placeholder="Details..." autoFocus />
            <div className="composer-actions">
              <button className="text-button" onClick={handleCancelEdit}>Cancel</button>
              <button className="community-ask-btn small" onClick={handleSaveEdit}>Save</button>
            </div>
          </div>
        ) : (
          <>
            <h3>{question.title}</h3>
            <p>{question.body}</p>
          </>
        )}

        <div className="tag-row">
          {question.tags.map((t) => (
            <span key={t} className="tag-chip">
              {t}
            </span>
          ))}
        </div>
        <div className="comment-actions">
          <button onClick={() => setReplyOpen((v) => !v)}>
            <MessageSquare /> Reply
          </button>
          <span className="answer-count">
            {question.answers.length} answer{question.answers.length === 1 ? '' : 's'}
          </span>
        </div>
        {replyOpen && (
          <ReplyBox
            placeholder={question.answers.length === 0 ? 'Be the first to answer...' : 'Add your answer...'}
            onCancel={() => setReplyOpen(false)}
            onSubmit={(text) => {
              onAddAnswer(question.id, text)
              setReplyOpen(false)
            }}
          />
        )}
        {question.answers.length > 0 && (
          <div className="answer-list">
            {question.answers.map((a) => (
              <AnswerRow key={a.id} questionId={question.id} answer={a} myVotes={myVotes} onVote={onVote} onAddReply={onAddReply} />
            ))}
          </div>
        )}
      </div>
    </article>
  )
}

export default function CommunityPage() {
  const [profile] = useLocalState<Profile>('mitra_profile', defaultProfile)
  const [questions, setQuestions] = useLocalState<CommunityQuestion[]>('mitra_community', seedQuestions)
  const [myVotes, setMyVotes] = useLocalState<Votes>('mitra_community_votes', {})
  const [sort, setSort] = useState<SortMode>('top')
  const [composerOpen, setComposerOpen] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newBody, setNewBody] = useState('')
  const [newTags, setNewTags] = useState<string[]>([])

  function vote(id: string, dir: 1 | -1) {
    const current = myVotes[id] ?? 0
    const next = current === dir ? 0 : dir
    const delta = next - current
    setMyVotes((prev) => {
      const copy = { ...prev }
      if (next === 0) delete copy[id]
      else copy[id] = next
      return copy
    })
    setQuestions((prev) => applyDelta(prev, id, delta))
  }

  function addAnswer(questionId: string, body: string) {
    const answer: CommunityAnswer = {
      id: `${questionId}-a-${Date.now()}`,
      author: profile.name,
      initials: profile.initials,
      time: 'Just now',
      body: body.trim(),
      votes: 0,
      replies: [],
    }
    setQuestions((prev) => prev.map((q) => (q.id === questionId ? { ...q, answers: [...q.answers, answer] } : q)))
  }

  function addReply(questionId: string, answerId: string, body: string) {
    const reply: CommunityReply = {
      id: `${answerId}-r-${Date.now()}`,
      author: profile.name,
      initials: profile.initials,
      time: 'Just now',
      body: body.trim(),
      votes: 0,
    }
    setQuestions((prev) =>
      prev.map((q) =>
        q.id !== questionId
          ? q
          : { ...q, answers: q.answers.map((a) => (a.id === answerId ? { ...a, replies: [...a.replies, reply] } : a)) },
      ),
    )
  }

  function postQuestion() {
    if (!newTitle.trim() || !newBody.trim()) return
    const q: CommunityQuestion = {
      id: `q-${Date.now()}`,
      title: newTitle.trim(),
      body: newBody.trim(),
      tags: newTags,
      author: profile.name,
      initials: profile.initials,
      time: 'Just now',
      votes: 0,
      answers: [],
    }
    setQuestions((prev) => [q, ...prev])
    setNewTitle('')
    setNewBody('')
    setNewTags([])
    setComposerOpen(false)
  }

  function editQuestion(questionId: string, title: string, body: string) {
    setQuestions((prev) =>
      prev.map((q) => (q.id === questionId ? { ...q, title, body, edited: true } : q)),
    )
  }

  function deleteQuestion(questionId: string) {
    setQuestions((prev) => prev.filter((q) => q.id !== questionId))
  }

  const base = sort === 'top' ? [...questions].sort((a, b) => b.votes - a.votes) : questions
  const visible = sort === 'unanswered' ? base.filter((q) => q.answers.length === 0) : base

  return (
    <div className="view community-view">
      <div className="view-header">
        <div>
          <p className="section-kicker">COMMUNITY</p>
          <h1>Ask your campus.</h1>
          <p className="view-sub">Get answers from students who&apos;ve been there.</p>
        </div>
        <button className="community-ask-btn" onClick={() => setComposerOpen((v) => !v)}>
          <Plus /> Ask a question
        </button>
      </div>

      {composerOpen && (
        <div className="community-composer">
          <input value={newTitle} onChange={(e) => setNewTitle(e.target.value)} placeholder="What's your question?" />
          <textarea
            value={newBody}
            onChange={(e) => setNewBody(e.target.value)}
            placeholder="Add any details that'll help people answer..."
          />
          <div className="tag-picker">
            {tagOptions.map((t) => (
              <button
                key={t}
                className={newTags.includes(t) ? 'active' : ''}
                onClick={() => setNewTags((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]))}
              >
                {t}
              </button>
            ))}
          </div>
          <div className="composer-actions">
            <button className="text-button" onClick={() => setComposerOpen(false)}>
              Cancel
            </button>
            <button className="community-ask-btn small" onClick={postQuestion}>
              Post question
            </button>
          </div>
        </div>
      )}

      <div className="discover-tabs">
        <button className={sort === 'top' ? 'active' : ''} onClick={() => setSort('top')}>
          Top
        </button>
        <button className={sort === 'new' ? 'active' : ''} onClick={() => setSort('new')}>
          New
        </button>
        <button className={sort === 'unanswered' ? 'active' : ''} onClick={() => setSort('unanswered')}>
          Unanswered
        </button>
      </div>

      <div className="community-list">
        {visible.map((q) => (
          <QuestionCard
            key={q.id}
            question={q}
            isOwn={q.author === profile.name}
            myVotes={myVotes}
            onVote={vote}
            onAddAnswer={addAnswer}
            onAddReply={addReply}
            onEdit={editQuestion}
            onDelete={deleteQuestion}
          />
        ))}
        {visible.length === 0 && <p className="view-sub">No questions here yet.</p>}
      </div>
    </div>
  )
}
