import { useMutation, useQuery } from '@tanstack/react-query';
import { chatApi } from '../api';
import type { ModelResponse } from '../api/types';

// 채팅 히스토리 조회 Hook
export const useModels = (enabled = true) => {
  return useQuery<ModelResponse[]>({
    queryKey: ['models'],
    queryFn: () => chatApi.getModels(),
    enabled: !!enabled,
    staleTime: 30 * 1000, // 30초
  });
};

// 메시지 전송 Hook
export const useSendMessage = () => {
  return useMutation({
    mutationFn: chatApi.sendMessage,
    onSuccess: (data) => {
      console.log('메시지 전송 성공:', data.message);
    },
    onError: (error) => {
      console.error('메시지 전송 실패:', error);
    },
  });
};

// 채팅 세션 생성 Hook
export const useCreateChatSession = () => {
  return useMutation({
    mutationFn: chatApi.createSession,
    onSuccess: (data) => {
      console.log('채팅 세션 생성 성공:', data.sessionId);
    },
  });
};

// 채팅 히스토리 조회 Hook
export const useChatHistory = (sessionId: string, enabled = true) => {
  return useQuery({
    queryKey: ['chat-history', sessionId],
    queryFn: () => chatApi.getHistory(sessionId),
    enabled: !!sessionId && enabled,
    staleTime: 30 * 1000, // 30초
  });
};

// 세션 삭제 Hook
export const useDeleteChatSession = () => {
  return useMutation({
    mutationFn: (sessionId: string) => chatApi.deleteSession(sessionId),
    onSuccess: () => {
      console.log('채팅 세션 삭제 성공');
    },
  });
};
