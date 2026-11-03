'use client'

import { useCallback, useEffect, useState } from 'react'
import { BadgeCheck, Bot, ChevronDown, MessageSquare, RotateCcw, Search, ShieldCheck, Trash2, X } from 'lucide-react'
import {
  adminApi,
  type AdminComment,
  type AdminPost,
  type AdminView,
  type ReplyTemplate,
} from '@/lib/api'
import { useAdminError } from '@/lib/use-admin-error'

const views: { label: string; value: AdminView }[] = [
  { label: 'All', value: 'all' },
  { label: 'Unanswered', value: 'unanswered' },
  { label: 'Popular (50+)', value: 'popular' },
  { label: 'Verified', value: 'verified' },
  { label: 'In chatbot dataset', value: 'dataset' },
  { label: 'Deleted', value: 'deleted' },
]

type Templates = { reply: ReplyTemplate[]; reasons: string[]; threshold: number }

/** Inline composer for an official reply: pick a template (editable) or write one. */
function OfficialComposer({
  templates,
  target,
  onSend,
  onCancel,
}: {
  templates: ReplyTemplate[]
  target: string
  onSend: (body: string, templateKey?: string) => Promise<void>
  onCancel: () => void
}) {
  const [templateKey, setTemplateKey] = useState('')
  const [body, setBody] = useState('')
  const [sending, setSending] = useState(false)
  const chosen = templates.find((t) => t.key === templateKey)

  return (
    <div className="admin-composer">
      <div className="admin-composer-head">
        <ShieldCheck /> Replying as <strong>MITra Official</strong> to {target}
      </div>
      <select
        value={templateKey}
        onChange={(e) => {
          const t = templates.find((x) => x.key === e.target.value)
          setTemplateKey(e.target.value)
          if (t) setBody(t.text)
        }}
        aria-label="Reply template"
      >
        <option value="">Write my own reply…</option>
        {templates.map((t) => (
          <option key={t.key} value={t.key}>
            Template: {t.label}
          </option>
        ))}
      </select>
      <textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Your official reply…" autoFocus />
      <div className="composer-actions">
        <button className="text-button" onClick={onCancel}>
          Cancel
        </button>
        <button
          className="community-ask-btn small"
          disabled={!body.trim() || sending}
          onClick={async () => {
            setSending(true)
            // Only tag the template if it was sent unchanged, so the audit log stays accurate.
            await onSend(body.trim(), chosen && chosen.text === body.trim() ? chosen.key : undefined)
            setSending(false)
          }}
        >
          {sending ? 'Sending…' : 'Send official reply'}
        </button>
      </div>
    </div>
  )
}

/** Reason picker shown before any admin deletion. */
function DeleteConfirm({
  reasons,
  what,
  onConfirm,
  onCancel,
}: {
  reasons: string[]
  what: string
  onConfirm: (reason: string, note: string) => Promise<void>
  onCancel: () => void
}) {
  const [reason, setReason] = useState('')
  const [note, setNote] = useState('')
  return (
    <div className="admin-delete-confirm" role="alertdialog" aria-label={`Delete ${what}`}>
      <p>
        Delete this {what}? Students will no longer see it, and the author is told the reason. You can restore it later from
        the Deleted tab.
      </p>
      <div className="tag-picker">
        {reasons.map((r) => (
          <button key={r} className={reason === r ? 'active' : ''} onClick={() => setReason(r)}>
            {r}
          </button>
        ))}
      </div>
      <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Optional note to the author" maxLength={300} />
      <div className="composer-actions">
        <button className="text-button" onClick={onCancel} autoFocus>
          Cancel
        </button>
        <button className="community-ask-btn small danger" disabled={!reason} onClick={() => onConfirm(reason, note)}>
          Delete {what}
        </button>
      </div>
    </div>
  )
}

function DeletedNote({ info }: { info: NonNullable<AdminComment['deleted']> }) {
  return (
    <span className="admin-deleted-note">
      <Trash2 /> Deleted by {info.by} · {info.reason ?? 'no reason'} · {info.time}
    </span>
  )
}

function AdminThread({
  comment,
  depth,
  templates,
  act,
  postId,
}: {
  comment: AdminComment
  depth: number
  templates: Templates
  act: (fn: () => Promise<unknown>) => Promise<void>
  postId: string
}) {
  const [mode, setMode] = useState<'none' | 'reply' | 'delete'>('none')
  return (
    <div className={`admin-comment ${comment.deleted ? 'is-deleted' : ''}`} style={{ marginLeft: Math.min(depth, 4) * 18 }}>
      <div className="community-meta">
        <strong>{comment.author}</strong>
        {comment.is_official && (
          <span className="official-tag">
            <BadgeCheck /> Official
          </span>
        )}
        <time>{comment.time}</time>
        {comment.edited && <span className="edited-tag">edited</span>}
        <span className="admin-score">{comment.votes} pts</span>
        <div className="own-post-actions">
          {comment.deleted ? (
            <button className="icon-action" title="Restore reply" aria-label="Restore reply" onClick={() => act(() => adminApi.restoreComment(comment.id))}>
              <RotateCcw size={14} />
            </button>
          ) : (
            <>
              <button className="icon-action" title="Reply officially to this" aria-label="Reply officially" onClick={() => setMode('reply')}>
                <MessageSquare size={14} />
              </button>
              <button className="icon-action danger" title="Delete reply" aria-label="Delete reply" onClick={() => setMode('delete')}>
                <Trash2 size={14} />
              </button>
            </>
          )}
        </div>
      </div>
      <p>{comment.body}</p>
      {comment.deleted && <DeletedNote info={comment.deleted} />}
      {mode === 'reply' && (
        <OfficialComposer
          templates={templates.reply}
          target={comment.author}
          onCancel={() => setMode('none')}
          onSend={(body, key) => act(() => adminApi.reply(postId, body, comment.id, key)).then(() => setMode('none'))}
        />
      )}
      {mode === 'delete' && (
        <DeleteConfirm
          reasons={templates.reasons}
          what="reply"
          onCancel={() => setMode('none')}
          onConfirm={(reason, note) => act(() => adminApi.deleteComment(comment.id, reason, note)).then(() => setMode('none'))}
        />
      )}
      {comment.replies.map((r) => (
        <AdminThread key={r.id} comment={r} depth={depth + 1} templates={templates} act={act} postId={postId} />
      ))}
    </div>
  )
}

function PostCard({ post, templates, act }: { post: AdminPost; templates: Templates; act: (fn: () => Promise<unknown>) => Promise<void> }) {
  const [open, setOpen] = useState(false)
  const [mode, setMode] = useState<'none' | 'reply' | 'delete'>('none')

  return (
    <article className={`utility-card admin-post ${post.deleted ? 'is-deleted' : ''}`}>
      <div className="community-meta">
        <strong>{post.author}</strong>
        <time>{post.time}</time>
        {post.verified && (
          <span className="verified-post-tag">
            <BadgeCheck /> Verified{post.verified_by ? ` by ${post.verified_by}` : ''}
          </span>
        )}
        {post.in_dataset && (
          <span className={`admin-dataset-tag ${post.dataset_source === 'community_popular' ? 'popular' : ''}`}>
            <Bot /> In chatbot dataset ({post.dataset_source === 'community_verified' ? 'verified' : 'popular'})
          </span>
        )}
        {post.has_official_reply && (
          <span className="official-tag">
            <ShieldCheck /> Answered officially
          </span>
        )}
      </div>
      <h3>{post.title}</h3>
      <p className="admin-post-body">{post.body}</p>
      {post.deleted && <DeletedNote info={post.deleted} />}
      <div className="tag-row">
        {post.tags.map((t) => (
          <span key={t} className="tag-chip">
            {t}
          </span>
        ))}
      </div>
      <div className="admin-post-stats">
        <span>
          <b>{post.votes}</b> score
        </span>
        <span title={`${templates.threshold} upvotes from distinct students add a post to the chatbot dataset`}>
          <b>{post.upvotes}</b>/{templates.threshold} upvotes
        </span>
        <span>
          <b>{post.answer_count}</b> answer{post.answer_count === 1 ? '' : 's'}
        </span>
      </div>

      <div className="admin-actions">
        {post.deleted ? (
          <button className="network-action" onClick={() => act(() => adminApi.restorePost(post.id))}>
            <RotateCcw /> Restore post
          </button>
        ) : (
          <>
            <button className="network-action" onClick={() => setMode(mode === 'reply' ? 'none' : 'reply')}>
              <ShieldCheck /> Reply as Official
            </button>
            <button
              className="network-action connected"
              onClick={() => act(() => adminApi.verify(post.id, !post.verified))}
              title={post.verified ? 'Remove the Verified tag' : 'Mark verified and add to the chatbot dataset'}
            >
              <BadgeCheck /> {post.verified ? 'Unverify' : 'Verify'}
            </button>
            <button className="network-action ghost" onClick={() => setMode(mode === 'delete' ? 'none' : 'delete')}>
              <Trash2 /> Delete
            </button>
          </>
        )}
        {post.answers.length > 0 && (
          <button className="text-button admin-thread-toggle" onClick={() => setOpen((v) => !v)}>
            {open ? 'Hide' : 'Show'} thread <ChevronDown className={open ? 'open' : ''} />
          </button>
        )}
      </div>

      {mode === 'reply' && (
        <OfficialComposer
          templates={templates.reply}
          target="the question"
          onCancel={() => setMode('none')}
          onSend={(body, key) => act(() => adminApi.reply(post.id, body, undefined, key)).then(() => setMode('none'))}
        />
      )}
      {mode === 'delete' && (
        <DeleteConfirm
          reasons={templates.reasons}
          what="question"
          onCancel={() => setMode('none')}
          onConfirm={(reason, note) => act(() => adminApi.deletePost(post.id, reason, note)).then(() => setMode('none'))}
        />
      )}
      {open && (
        <div className="admin-thread">
          {post.answers.map((c) => (
            <AdminThread key={c.id} comment={c} depth={0} templates={templates} act={act} postId={post.id} />
          ))}
        </div>
      )}
    </article>
  )
}

export default function AdminCommunityPage() {
  const [view, setView] = useState<AdminView>('all')
  const [posts, setPosts] = useState<AdminPost[]>([])
  const [counts, setCounts] = useState<Partial<Record<AdminView, number>>>({})
  const [templates, setTemplates] = useState<Templates>({ reply: [], reasons: [], threshold: 50 })
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const handleError = useAdminError(setError)

  const load = useCallback(async () => {
    try {
      const data = await adminApi.posts(view)
      setPosts(data.posts)
      setCounts(data.counts)
      setError(null)
    } catch (e) {
      handleError(e)
    } finally {
      setLoading(false)
    }
  }, [view, handleError])

  useEffect(() => {
    setLoading(true)
    load()
  }, [load])

  useEffect(() => {
    adminApi
      .templates()
      .then((t) => setTemplates({ reply: t.reply_templates, reasons: t.delete_reasons, threshold: t.popular_threshold }))
      .catch(handleError)
  }, [handleError])

  async function act(fn: () => Promise<unknown>) {
    try {
      await fn()
    } catch (e) {
      handleError(e)
    }
    await load()
  }

  const q = query.trim().toLowerCase()
  const visible = q ? posts.filter((p) => `${p.title} ${p.body} ${p.author} ${p.tags.join(' ')}`.toLowerCase().includes(q)) : posts

  return (
    <div className="view admin-view">
      <div className="view-header">
        <div>
          <p className="section-kicker">ADMIN · COMMUNITY</p>
          <h1>Community moderation.</h1>
          <p className="view-sub">
            Reply as MITra Official, verify good answers for the chatbot, and remove anything inappropriate. Every action is
            logged under your name.
          </p>
        </div>
      </div>

      <div className="large-search community-search admin-search">
        <Search />
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filter by title, text, author or tag" aria-label="Filter posts" />
        {q && (
          <button className="icon-action" onClick={() => setQuery('')} aria-label="Clear filter">
            <X size={14} />
          </button>
        )}
      </div>

      <div className="discover-tabs">
        {views.map((v) => (
          <button key={v.value} className={view === v.value ? 'active' : ''} onClick={() => setView(v.value)}>
            {v.label} {counts[v.value] !== undefined && <span className="admin-count">{counts[v.value]}</span>}
          </button>
        ))}
      </div>

      {error && (
        <div className="community-error" role="alert">
          <span>{error}</span>
          <button className="text-button" onClick={() => load()}>
            Try again
          </button>
        </div>
      )}
      <div className="admin-post-list">
        {loading && <p className="view-sub">Loading…</p>}
        {!loading && visible.map((p) => <PostCard key={p.id} post={p} templates={templates} act={act} />)}
        {!loading && !error && visible.length === 0 && <p className="view-sub">Nothing here.</p>}
      </div>
    </div>
  )
}
