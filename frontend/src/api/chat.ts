import { apiClient } from "./client";
import type { ChatAskRequest, ChatResponse } from "../types/chat";

export async function askChat(payload: ChatAskRequest): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>("/api/chat/ask", payload);
  return response.data;
}