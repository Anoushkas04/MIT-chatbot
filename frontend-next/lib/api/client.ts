import type { ApiErrorBody } from "./types";

const DEFAULT_TIMEOUT_MS = 10_000;
const DEFAULT_GET_RETRIES = 1;

export function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
}

export function resolveApiUrl(path: string): string {
  return `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
}

export class ApiError extends Error {
  readonly status: number;
  readonly body: ApiErrorBody | null;

  constructor(message: string, status: number, body: ApiErrorBody | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export interface ApiRequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  timeoutMs?: number;
  retries?: number;
  token?: string | null;
}

async function parseResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") || "";
  if (response.status === 204) return null;
  if (contentType.includes("application/json")) return response.json();
  return response.text();
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const {
    body,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    retries: configuredRetries,
    token,
    headers: initialHeaders,
    ...requestInit
  } = options;
  const method = (requestInit.method || "GET").toUpperCase();
  const retries = configuredRetries ?? (method === "GET" ? DEFAULT_GET_RETRIES : 0);
  const url = `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const headers = new Headers(initialHeaders);
      if (body !== undefined) headers.set("Content-Type", "application/json");
      if (token) headers.set("Authorization", `Bearer ${token}`);

      const response = await fetch(url, {
        ...requestInit,
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: controller.signal,
      });
      const responseBody = await parseResponseBody(response);

      if (!response.ok) {
        const errorBody = typeof responseBody === "object" && responseBody !== null
          ? responseBody as ApiErrorBody
          : null;
        const message = errorBody?.detail || errorBody?.message || `Request failed with status ${response.status}`;
        throw new ApiError(message, response.status, errorBody);
      }

      return responseBody as T;
    } catch (error) {
      const retryable = !(error instanceof ApiError) || error.status >= 500;
      if (!retryable || attempt === retries) {
        if (error instanceof DOMException && error.name === "AbortError") {
          throw new ApiError(`Request timed out after ${timeoutMs}ms`, 408);
        }
        throw error;
      }
    } finally {
      clearTimeout(timeout);
    }
  }

  throw new ApiError("Request failed", 500);
}

