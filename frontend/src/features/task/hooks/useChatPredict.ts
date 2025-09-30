import { api } from '@/shared';
import { useMutation } from '@tanstack/react-query';
import type { ChatPredictRequest, ChatPredictResponse } from '../types';

// 채팅 예측 API
const chatPredict = async (
  request: ChatPredictRequest
): Promise<ChatPredictResponse> => {
  const response = await api.post(`/pipelines/predict`, request, {
    headers: {
      accept: 'application/json',
      'Content-Type': 'application/json',
    },
  });
  return response.data;
};

// 채팅 예측 hook
export const useChatPredict = () => {
  return useMutation({
    mutationFn: chatPredict,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};
