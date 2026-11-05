'use client'

import { Suspense, useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowBigDown, ArrowBigUp, BadgeCheck, MessageSquare, Pencil, Plus, Search, Trash2, X } from 'lucide-react'
import type { CommunityComment, CommunityQuestion } from '@/lib/mock-data'
import { MIN_RELEVANCE, matchTopics, scoreQuestion } from '@/lib/community-search'
import { communityApi } from '@/lib/api'

// Past this depth sub-threads stop indenting further so deep chains stay readable.
const MAX_INDENT_DEPTH = 4
const tagOptions = ['Academics', 'Attendance', 'Exams', 'Hostel', 'Campus Life', 'Clubs', 'Opportunities', 'Registration']

type SortMode = 'top' | 'new' | 'unanswered'
type Votes = Record<string, 1 | -1>

function mapComment(list: CommunityComment[], id: string, fn: (c: CommunityComment) => CommunityComment): CommunityComment[] {
  return list.map((c) => (c.id === id ? fn(c) : { ...c, replies: mapComment(c.replies ?? [], id, fn) }))
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

// Admin accounts post as "MITra Official"; they're the only verified accounts.
function OfficialBadge() {
  return (
    <span className="official-tag">
      <BadgeCheck /> Official
    </span>
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
  myVotes: Votes
  onVote: (id: string, dir: 1 | -1) => void
  onReply: (parentId: string, body: string) => void
  onEdit: (id: string, body: string) => void
  onDelete: (id: string) => void
}

function CommentThread({ comment, depth, ...handlers }: { comment: CommunityComment; depth: number } & ThreadHandlers) {
  const { myVotes, onVote, onReply, onEdit, onDelete } = handlers
  const [replyOpen, setReplyOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const isTop = depth === 0
  const isOwn = !comment.deleted && !!comment.isMine

  return (
    <div className={isTop ? 'answer-row' : 'reply-row'}>
      <span className={`${isTop ? 'comment-avatar' : 'comment-avatar small'}${comment.isOfficial && !comment.deleted ? ' official' : ''}`}>
        {comment.deleted ? '?' : comment.initials}
      </span>
      <div className="answer-body">
        <div className="community-meta">
          <strong>{comment.deleted ? '[deleted]' : comment.author}</strong>
          {comment.isOfficial && !comment.deleted && <OfficialBadge />}
          <time>{comment.time}</time>
          {comment.edited && !comment.deleted && <span className="edited-tag">edited</span>}
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
  const isOwn = !!question.isMine

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
          <span className={`comment-avatar${question.isOfficial ? ' official' : ''}`}>{question.initials}</span>
          <strong>{question.author}</strong>
          {question.isOfficial && <OfficialBadge />}
          <time>{question.time}</time>
          {question.edited && <span className="edited-tag">edited</span>}
          {question.verified && (
            <span className="verified-post-tag" title="Checked by the MITra team">
              <BadgeCheck /> Verified
            </span>
          )}
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
  return (
    <Suspense fallback={null}>
      <CommunityInner />
    </Suspense>
  )
}

function CommunityInner() {
  // Chat citations link here with ?q=<post title>
  const params = useSearchParams()
  const [questions, setQuestions] = useState<CommunityQuestion[]>([])
  const [myVotes, setMyVotes] = useState<Votes>({})
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [sort, setSort] = useState<SortMode>('top')
  const [interest, setInterest] = useState('All')
  const [query, setQuery] = useState(params.get('q') ?? '')
  const [composerOpen, setComposerOpen] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newBody, setNewBody] = useState('')
  const [newTags, setNewTags] = useState<string[]>([])

  const refresh = useCallback(async () => {
    try {
      const feed = await communityApi.list()
      setQuestions(feed.questions)
      setMyVotes(feed.myVotes)
      setLoadError(null)
      // Notifications (and the sidebar's unread count) read this cached copy.
      try {
        localStorage.setItem('mitra_community', JSON.stringify(feed.questions))
        localStorage.setItem('mitra_community_votes', JSON.stringify(feed.myVotes))
      } catch {}
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Couldn't load the community.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  function showError(e: unknown, fallback: string) {
    setActionError(e instanceof Error ? e.message : fallback)
    setTimeout(() => setActionError(null), 5000)
  }

  // Runs a write, shows its error briefly if it fails, and reloads the feed either way.
  async function run(action: () => Promise<unknown>) {
    try {
      await action()
    } catch (e) {
      showError(e, 'Something went wrong. Please try again.')
    }
    await refresh()
  }

  function vote(id: string, dir: 1 | -1) {
    const current = myVotes[id] ?? 0
    const next = current === dir ? 0 : dir
    // Optimistic: update the count now, then confirm with the server.
    setMyVotes((prev) => {
      const copy = { ...prev }
      if (next === 0) delete copy[id]
      else copy[id] = next
      return copy
    })
    setQuestions((prev) => applyDelta(prev, id, next - current))
    communityApi.vote(id, next).catch((e) => {
      showError(e, "Your vote wasn't saved.")
      refresh()
    })
  }

  const addAnswer = (questionId: string, body: string) => run(() => communityApi.comment(questionId, body.trim()))
  const addReply = (questionId: string, parentId: string, body: string) =>
    run(() => communityApi.comment(questionId, body.trim(), parentId))
  const editComment = (_questionId: string, id: string, body: string) => run(() => communityApi.editComment(id, body.trim()))
  const deleteComment = (_questionId: string, id: string) => run(() => communityApi.deleteComment(id))
  const editQuestion = (questionId: string, title: string, body: string) => run(() => communityApi.editPost(questionId, title, body))
  const deleteQuestion = (questionId: string) => run(() => communityApi.deletePost(questionId))

  async function postQuestion() {
    if (!newTitle.trim() || !newBody.trim()) return
    try {
      await communityApi.create(newTitle.trim(), newBody.trim(), newTags)
    } catch (e) {
      // Keep the draft so nothing typed is lost when the server refuses it.
      showError(e, "Your question wasn't posted.")
      return
    }
    setNewTitle('')
    setNewBody('')
    setNewTags([])
    setComposerOpen(false)
    await refresh()
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
          <p className="view-sub">
            Get answers from students who&apos;ve been there.{' '}
            <Link href="/guidelines" className="guidelines-link">
              Community Guidelines
            </Link>
          </p>
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
          <p className="guidelines-note">
            Keep it respectful and accurate, and leave out anyone&apos;s personal details.{' '}
            <Link href="/guidelines">Read the guidelines</Link>
          </p>
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

      {actionError && (
        <p className="community-error" role="alert">
          {actionError}
          {/* Posts the moderation check blocks come back with this wording (community_v2.py) */}
          {actionError.includes('Community Guidelines') && (
            <>
              {' '}
              <Link href="/guidelines#consequences" className="guidelines-link">
                See the guidelines
              </Link>
            </>
          )}
        </p>
      )}

      <div className="community-list">
        {loading && <p className="view-sub">Loading questions…</p>}
        {!loading && loadError && (
          <div className="community-error" role="alert">
            <span>{loadError}</span>
            <button className="text-button" onClick={() => refresh()}>
              Try again
            </button>
          </div>
        )}
        {visible.map((q) => (
          <QuestionCard
            key={q.id}
            question={q}
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
        {!loading && !loadError && visible.length === 0 && (
          <p className="view-sub">{searching ? `No questions match "${query.trim()}".` : 'No questions here yet. Be the first to ask!'}</p>
        )}
      </div>
    </div>
  )
}
