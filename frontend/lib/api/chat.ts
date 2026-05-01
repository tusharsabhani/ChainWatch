import { apiRequest } from "@/lib/api/client";
import type {
  ChatCreateSessionRequest,
  ChatCreateSessionResponse,
  ChatMessagesResponse,
  ChatPostMessageRequest,
  ChatPostMessageResponse,
  ChatSessionsResponse
} from "@/lib/api/types";

export function getChatSessions() {
  return apiRequest<ChatSessionsResponse>("chat/sessions");
}

export function createChatSession(payload: ChatCreateSessionRequest) {
  return apiRequest<ChatCreateSessionResponse>("chat/sessions", {
    method: "POST",
    body: payload
  });
}

export function getChatMessages(sessionId: string) {
  return apiRequest<ChatMessagesResponse>(`chat/sessions/${sessionId}/messages`);
}

export function postChatMessage(payload: ChatPostMessageRequest) {
  return apiRequest<ChatPostMessageResponse>("chat/messages", {
    method: "POST",
    body: payload
  });
}
