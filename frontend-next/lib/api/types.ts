export interface HealthResponse {
  status: "ok" | string;
  platform: string;
  rag_store_ready: boolean;
  docs_url: string;
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

