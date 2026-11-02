'use client'

import { useEffect, useState } from 'react'
import { AlertCircle, Check, LockKeyhole, MessageCircle, ThumbsDown, ThumbsUp, Trophy } from 'lucide-react'
import { getCommunityLeaderboard, getCommunityPosts, type CommunityLeader, type CommunityPost } from '@/lib/api'

const categories = ['all', 'Academics', 'Hostels', 'Mess', 'Clubs', 'Events', 'Transportation', 'Resources']

export function CommunityView() {
  const [category, setCategory] = useState('all')
  const [posts, setPosts] = useState<CommunityPost[]>([])
  const [leaders, setLeaders] = useState<CommunityLeader[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  useEffect(() => { let active = true; Promise.all([getCommunityPosts(category), getCommunityLeaderboard()]).then(([items, board]) => { if (active) { setPosts(items); setLeaders(board) } }).catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'Community could not be loaded.') }).finally(() => { if (active) setLoading(false) }); return () => { active = false } }, [category])
  const selectCategory = (item: string) => { setLoading(true); setError(''); setCategory(item) }
  return <div className="view"><div className="view-header"><div><p className="section-kicker">STUDENT COMMUNITY · READ ONLY</p><h1>What students are sharing.</h1><p className="view-sub">Browse real seeded community records. Posting and voting require authentication.</p></div><button className="guest-disabled" disabled><LockKeyhole /> Sign in to post</button></div><div className="filter-row">{categories.map(item => <button key={item} className={category === item ? 'active' : ''} onClick={() => selectCategory(item)}>{item}</button>)}</div>{error && <div className="inline-error"><AlertCircle />{error}</div>}
    <div className="community-layout"><div className="community-feed">{loading && <p className="loading-copy">Loading discussions…</p>}{!loading && posts.length === 0 && <div className="empty-state"><MessageCircle /><h3>No discussions in this category</h3></div>}{posts.map(post => <article className="community-post" key={post.id}><div className="post-meta"><span>{post.sub_community}</span><small>{post.author} · {post.time}</small>{post.verified && <b><Check /> Verified</b>}</div><h3>{post.title}</h3><p>{post.content}</p><div className="post-stats"><span><ThumbsUp />{post.upvotes}</span><span><ThumbsDown />{post.downvotes}</span><span><MessageCircle />{post.comments.length}</span></div>{post.comments.filter(comment => comment.is_helpful).slice(0,1).map(comment => <blockquote key={comment.id}><Check /> <span><b>Helpful answer from {comment.author}</b>{comment.content}</span></blockquote>)}</article>)}</div>
      <aside className="leaderboard-card"><p className="section-kicker">CONTRIBUTORS</p><h3><Trophy /> Community leaderboard</h3>{leaders.length === 0 ? <p>No public contributor records yet.</p> : leaders.slice(0,5).map(leader => <div key={`${leader.rank}-${leader.name}`}><b>#{leader.rank}</b><span>{leader.name}</span><small>{leader.points} pts</small></div>)}</aside></div>
  </div>
}
