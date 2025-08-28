// API 요청/응답 타입 정의
export interface SendMessageRequest {
  message: string;
  sessionId?: string;
}

export interface SendMessageResponse {
  message: string;
  timestamp: string;
  sessionId: string;
}

export interface ChatSessionRequest {
  userId?: string;
}

export interface ChatSessionResponse {
  sessionId: string;
  createdAt: string;
}

export interface ChatHistoryResponse {
  messages: {
    id: string;
    content: string;
    sender: 'user' | 'bot';
    timestamp: string;
  }[];
  sessionId: string;
}

export interface ModelResponse {}
