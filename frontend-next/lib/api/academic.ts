import { apiRequest } from "./client";
import type { NotificationsResponse, TimelineResponse } from "./types";

export const getTimeline = () => apiRequest<TimelineResponse>("/api/academic/timeline?role=student");
export const getNotifications = () => apiRequest<NotificationsResponse>("/api/notifications?user_id=guest-integration&role=student");
