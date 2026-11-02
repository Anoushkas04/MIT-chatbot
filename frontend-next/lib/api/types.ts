export interface HealthResponse {
  status: "ok" | string;
  platform: string;
  rag_store_ready: boolean;
  rag_chunk_count?: number;
  rag_error?: string | null;
  docs_url: string;
}

export interface ChatCitation {
  source: string; snippet: string; score: number; document_id?: string; page_number?: number;
  retrieval_method?: string; source_url?: string;
}
export interface ChatRequest {
  message: string;
  session_id: string;
  role?: string;
  language?: string;
  department?: string;
  academic_year?: string;
  semester?: string;
}
export interface ChatResponse {
  text: string; sources: string[]; citations: ChatCitation[]; confidence: string;
  confidence_type: string; followups: string[]; provider: string; model: string;
  verification_warnings: string[];
}

export interface TimelineEvent {
  id: number; title: string; description: string; category: string; icon: string;
  start_datetime: string; formatted_date: string; source: string; status: string;
  time_string: string; countdown_label: string; urgency: string;
}
export interface TimelineResponse { count: number; events: TimelineEvent[] }

export interface CampusNotification {
  state_id: number; title: string; content: string; time: string; category: string;
  priority: string; source_doc: string; read: boolean;
}
export interface NotificationsResponse { unread_count: number; notifications: CampusNotification[] }

export interface SearchResult {
  id: string; title: string; category: string; source_type: string; badge: string;
  snippet: string; link_target: string; relevance: number; source: string;
}
export interface SearchResponse {
  query: string; category: string; page: number; page_size: number; total_pages: number;
  total_results: number; official_count: number; community_count: number; results: SearchResult[];
}

export interface CommunityComment { id: number; author: string; content: string; is_helpful: boolean }
export interface CommunityPost {
  id: number; author: string; sub_community: string; tag: string; title: string; content: string;
  upvotes: number; downvotes: number; verified: boolean; time: string; comments: CommunityComment[];
}
export interface CommunityLeader { rank: number; name: string; points: number; helpful_answers?: number; badge?: string }

export interface FacultyMember {
  id: string; name: string; dept: string; designation: string; cabin: string | null;
  email: string; qualification: string; source: string;
}
export interface FacultyResponse {
  count: number; page: number; page_size: number; total_pages: number; data: FacultyMember[];
}

export interface Department {
  id: number;
  code: string;
  name: string;
  school: string | null;
  building: string | null;
}

export interface DepartmentsResponse {
  count: number;
  departments: Department[];
}

export interface ApiErrorBody {
  detail?: string;
  message?: string;
  [key: string]: unknown;
}

