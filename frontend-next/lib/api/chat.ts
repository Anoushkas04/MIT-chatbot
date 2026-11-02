import { apiRequest } from "./client";
import type { ChatRequest, ChatResponse } from "./types";

export function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  return apiRequest<ChatResponse>("/api/chat", { method: "POST", body: request, timeoutMs: 30_000 });
}
