import { apiRequest } from './client'
import type { FacultyResponse } from './types'

export function getFaculty(query: string, page = 1): Promise<FacultyResponse> {
  const params = new URLSearchParams({ query, page: String(page), page_size: '20' })
  return apiRequest<FacultyResponse>(`/api/faculty?${params}`)
}
