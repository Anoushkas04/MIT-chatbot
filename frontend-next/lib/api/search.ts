import { apiRequest } from "./client";
import type { SearchResponse } from "./types";

export function searchCampus(query: string, category: string, page: number): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query, category, page: String(page), page_size: "8" });
  return apiRequest<SearchResponse>(`/api/search?${params}`);
}
