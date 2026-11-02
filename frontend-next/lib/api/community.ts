import { apiRequest } from './client'
import type { CommunityLeader, CommunityPost } from './types'

export function getCommunityPosts(category = 'all'): Promise<CommunityPost[]> {
  return apiRequest<CommunityPost[]>(`/api/posts?category=${encodeURIComponent(category)}`)
}

export function getCommunityLeaderboard(): Promise<CommunityLeader[]> {
  return apiRequest<CommunityLeader[]>('/api/posts/leaderboard')
}
