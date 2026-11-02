import { apiRequest } from "./client";
import type { DepartmentsResponse, HealthResponse } from "./types";

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/api/health");
}

export function getDepartments(): Promise<DepartmentsResponse> {
  return apiRequest<DepartmentsResponse>("/api/departments");
}

