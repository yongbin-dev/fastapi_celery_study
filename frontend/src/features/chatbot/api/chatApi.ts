import { api } from '@/shared/utils/api';
import type {
  SendMessageRequest,
  SendMessageResponse,
  ChatSessionRequest,
  ChatSessionResponse,
  ChatHistoryResponse,
  ModelResponse,
} from './types';

// 챗봇 API 엔드포인트들
export const chatApi = {
  // 채팅 히스토리 조회
  getModels: async (): Promise<ModelResponse[]> => {
    const response = await api.get<ModelResponse[]>(`/health`);
    return response.data;
  },

  // 메시지 전송
  sendMessage: async (
    data: SendMessageRequest
  ): Promise<SendMessageResponse> => {
    const response = await api.post<SendMessageResponse>('/chat/message', data);
    return response.data;
  },

  // 채팅 세션 생성
  createSession: async (
    data: ChatSessionRequest
  ): Promise<ChatSessionResponse> => {
    const response = await api.post<ChatSessionResponse>('/chat/session', data);
    return response.data;
  },

  // 채팅 히스토리 조회
  getHistory: async (sessionId: string): Promise<ChatHistoryResponse> => {
    const response = await api.get<ChatHistoryResponse>(
      `/chat/history/${sessionId}`
    );
    return response.data;
  },

  // 세션 삭제
  deleteSession: async (sessionId: string): Promise<{ success: boolean }> => {
    const response = await api.delete<{ success: boolean }>(
      `/chat/session/${sessionId}`
    );
    return response.data;
  },
};
