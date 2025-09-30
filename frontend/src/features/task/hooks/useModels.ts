import { useQuery } from '@tanstack/react-query';

import { api } from '@/shared/utils/api';
import type { ModelsResponse } from '../types';

// 모델 리스트 조회 API
const fetchModels = async (): Promise<ModelsResponse> => {
  const response = await api.get(`/llm/models`, {
    headers: {
      accept: 'application/json',
    },
  });
  return response.data;
};

// 모델 리스트 조회 hook
export const useModels = () => {
  return useQuery({
    queryKey: ['models'],
    queryFn: fetchModels,
    staleTime: 5 * 60 * 1000, // 5분
    gcTime: 10 * 60 * 1000, // 10분
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};
