'use client'

import { useMemo, useState } from 'react'
import { ArrowBigDown, ArrowBigUp, BadgeCheck, MessageSquare, Pencil, Plus, Search, Trash2, X } from 'lucide-react'
import {
  communityQuestions as seedQuestions,
  defaultProfile,
  type CommunityComment,
  type CommunityQuestion,
  type Profile,
} from '@/lib/mock-data'
import { MIN_RELEVANCE, matchTopics, scoreQuestion } from '@/lib/community-search'
import { useLocalState } from '@/lib/use-local-state'

const VERIFIED_THRESHOLD = 10
// Past this depth sub-threads stop indenting further so deep chains stay readable.
const MAX_INDENT_DEPTH = 4
const tagOptions = ['Academics', 'Attendance', 'Exams', 'Hostel', 'Campus Life', 'Clubs', 'Opportunities', 'Registration']

type SortMode = 'top' | 'new' | 'unanswered'
type Votes = Record<string, 1 | -1>

// Stored data from before nesting existed has leaf replies without a `replies` array.
function normalizeComment(c: CommunityComment): CommunityComment {
  return { ...c, replies: (c.replies ?? []).map(normalizeComment) }
}

function mapComment(list: CommunityComment[], id: string, fn: (c: CommunityComment) => CommunityComment): CommunityComment[] {
  return list.map((c) => (c.id === id ? fn(c) : { ...c, replies: mapComment(c.replies ?? [], id, fn) }))
}

// A comment with replies becomes a placeholder so its sub-thread survives.
function removeComment(list: CommunityComment[], id: string): CommunityComment[] {
  return list.flatMap((c) => {
    const replies = c.replies ?? []
    if (c.id !== id) return [{ ...c, replies: removeComment(replies, id) }]
    return replies.length > 0 ? [{ ...c, body: '', deleted: true }] : []
  })
}

function applyDelta(list: CommunityQuestion[], id: string, delta: number): CommunityQuestion[] {
  return list.map((q) =>
    q.id === id
      ? { ...q, votes: q.votes + delta }
      : { ...q, answers: mapComment(q.answers, id, (c) => ({ ...c, votes: c.votes + delta })) },
  )
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

function ReplyBox({
  placeholder,
  initial = '',
  submitLabel = 'Post',
  onSubmit,
  onCancel,
}: {
  placeholder: string
  initial?: string
  submitLabel?: string
  onSubmit: (text: string) => void
  onCancel: () => void
}) {
  const [text, setText] = useState(initial)
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
          {submitLabel}
        </button>
      </div>
    </div>
  )
}

type ThreadHandlers = {
  currentUser: string
  myVotes: Votes
  onVote: (id: string, dir: 1 | -1) => void
  onReply: (parentId: string, body: string) => void
  onEdit: (id: string, body: string) => void
  onDelete: (id: string) => void
}

function CommentThread({ comment, depth, ...handlers }: { comment: CommunityComment; depth: number } & ThreadHandlers) {
  const { currentUser, myVotes, onVote, onReply, onEdit, onDelete } = handlers
  const [replyOpen, setReplyOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const isTop = depth === 0
  const isOwn = !comment.deleted && comment.author === currentUser
  const verified = isTop && !comment.deleted && comment.votes >= VERIFIED_THRESHOLD

  return (
    <div className={isTop ? 'answer-row' : 'reply-row'}>
      <span className={isTop ? 'comment-avatar' : 'comment-avatar small'}>{comment.deleted ? '?' : comment.initials}</span>
      <div className="answer-body">
        <div className="community-meta">
          <strong>{comment.deleted ? '[deleted]' : comment.author}</strong>
          <time>{comment.time}</time>
          {comment.edited && !comment.deleted && <span className="edited-tag">edited</span>}
          {verified && (
            <span className="verified-tag">
              <BadgeCheck /> Community verified
            </span>
          )}
          {isOwn && !editing && (
            <div className="own-post-actions">
              <button className="icon-action" onClick={() => setEditing(true)} aria-label="Edit reply" title="Edit">
                <Pencil size={14} />
              </button>
              <button className="icon-action danger" onClick={() => onDelete(comment.id)} aria-label="Delete reply" title="Delete">
                <Trash2 size={14} />
              </button>
            </div>
          )}
        </div>
        {editing ? (
          <ReplyBox
            placeholder="Edit your reply..."
            initial={comment.body}
            submitLabel="Save"
            onCancel={() => setEditing(false)}
            onSubmit={(text) => {
              onEdit(comment.id, text)
              setEditing(false)
            }}
          />
        ) : (
          <p className={comment.deleted ? 'deleted-body' : undefined}>{comment.deleted ? 'This reply was deleted.' : comment.body}</p>
        )}
        <div className="comment-actions">
          <VoteControl id={comment.id} votes={comment.votes} myVotes={myVotes} onVote={onVote} />
          {!comment.deleted && (
            <button onClick={() => setReplyOpen((v) => !v)}>
              <MessageSquare /> Reply
            </button>
          )}
        </div>
        {replyOpen && (
          <ReplyBox
            placeholder={`Reply to ${comment.author}...`}
            onCancel={() => setReplyOpen(false)}
            onSubmit={(text) => {
              onReply(comment.id, text)
              setReplyOpen(false)
            }}
          />
        )}
        {comment.replies.length > 0 && (
          <div className={depth + 1 >= MAX_INDENT_DEPTH ? 'reply-list flat' : 'reply-list'}>
            {comment.replies.map((r) => (
              <CommentThread key={r.id} comment={r} depth={depth + 1} {...handlers} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function QuestionCard({
  question,
  currentUser,
  myVotes,
  onVote,
  onAddAnswer,
  onAddReply,
  onEditComment,
  onDeleteComment,
  onEdit,
  onDelete,
}: {
  question: CommunityQuestion
  currentUser: string
  myVotes: Votes
  onVote: (id: string, dir: 1 | -1) => void
  onAddAnswer: (questionId: string, body: string) => void
  onAddReply: (questionId: string, parentId: string, body: string) => void
  onEditComment: (questionId: string, id: string, body: string) => void
  onDeleteComment: (questionId: string, id: string) => void
  onEdit: (questionId: string, title: string, body: string) => void
  onDelete: (questionId: string) => void
}) {
  const [replyOpen, setReplyOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(question.title)
  const [editBody, setEditBody] = useState(question.body)
  const isOwn = question.author === currentUser

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
              <CommentThread
                key={a.id}
                comment={a}
                depth={0}
                currentUser={currentUser}
                myVotes={myVotes}
                onVote={onVote}
                onReply={(parentId, body) => onAddReply(question.id, parentId, body)}
                onEdit={(id, body) => onEditComment(question.id, id, body)}
                onDelete={(id) => onDeleteComment(question.id, id)}
              />
            ))}
          </div>
        )}
      </div>
    </article>
  )
}

export default function CommunityPage() {
  const [profile] = useLocalState<Profile>('mitra_profile', defaultProfile)
  const [storedQuestions, setQuestions] = useLocalState<CommunityQuestion[]>('mitra_community', seedQuestions)
  const [myVotes, setMyVotes] = useLocalState<Votes>('mitra_community_votes', {})
  const [sort, setSort] = useState<SortMode>('top')
  const [interest, setInterest] = useState('All')
  const [query, setQuery] = useState('')
  const [composerOpen, setComposerOpen] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newBody, setNewBody] = useState('')
  const [newTags, setNewTags] = useState<string[]>([])

  const questions = storedQuestions.map((q) => ({ ...q, answers: q.answers.map(normalizeComment) }))

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

  function newComment(id: string, body: string): CommunityComment {
    return {
      id,
      author: profile.name,
      initials: profile.initials,
      time: 'Just now',
      body: body.trim(),
      votes: 0,
      replies: [],
    }
  }

  function updateAnswers(questionId: string, fn: (answers: CommunityComment[]) => CommunityComment[]) {
    setQuestions((prev) => prev.map((q) => (q.id === questionId ? { ...q, answers: fn(q.answers) } : q)))
  }

  function addAnswer(questionId: string, body: string) {
    const answer = newComment(`${questionId}-a-${Date.now()}`, body)
    updateAnswers(questionId, (answers) => [...answers, answer])
  }

  function addReply(questionId: string, parentId: string, body: string) {
    const reply = newComment(`${parentId}-r-${Date.now()}`, body)
    updateAnswers(questionId, (answers) => mapComment(answers, parentId, (c) => ({ ...c, replies: [...(c.replies ?? []), reply] })))
  }

  function editComment(questionId: string, id: string, body: string) {
    updateAnswers(questionId, (answers) => mapComment(answers, id, (c) => ({ ...c, body: body.trim(), edited: true })))
  }

  function deleteComment(questionId: string, id: string) {
    updateAnswers(questionId, (answers) => removeComment(answers, id))
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

  const searching = query.trim().length > 0
  const queryTopics = useMemo(() => (searching ? matchTopics(query) : []), [query, searching])

  const base = sort === 'top' ? [...questions].sort((a, b) => b.votes - a.votes) : questions
  const filtered = base.filter(
    (q) => (interest === 'All' || q.tags.includes(interest)) && (sort !== 'unanswered' || q.answers.length === 0),
  )
  // While searching, relevance replaces the Top/New ordering.
  const visible = searching
    ? filtered
        .map((q) => ({ q, score: scoreQuestion(q, query, queryTopics) }))
        .filter((r) => r.score >= MIN_RELEVANCE)
        .sort((a, b) => b.score - a.score)
        .map((r) => r.q)
    : filtered

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

      <div className="community-toolbar">
        <div className="large-search community-search">
          <Search />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search questions, e.g. 'midsem prep' or 'hostel wifi'"
            aria-label="Search community questions"
          />
          {searching && (
            <button className="icon-action" onClick={() => setQuery('')} aria-label="Clear search" title="Clear">
              <X size={14} />
            </button>
          )}
        </div>
        <select className="interest-select" value={interest} onChange={(e) => setInterest(e.target.value)} aria-label="Filter by interest">
          <option value="All">All interests</option>
          {tagOptions.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>
      {searching && (
        <p className="search-hint">
          {visible.length} result{visible.length === 1 ? '' : 's'}
          {queryTopics.length > 0 && <> · related to {queryTopics.slice(0, 3).join(', ')}</>}
        </p>
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
            currentUser={profile.name}
            myVotes={myVotes}
            onVote={vote}
            onAddAnswer={addAnswer}
            onAddReply={addReply}
            onEditComment={editComment}
            onDeleteComment={deleteComment}
            onEdit={editQuestion}
            onDelete={deleteQuestion}
          />
        ))}
        {visible.length === 0 && (
          <p className="view-sub">{searching ? `No questions match "${query.trim()}".` : 'No questions here yet.'}</p>
        )}
      </div>
    </div>
  )
}
