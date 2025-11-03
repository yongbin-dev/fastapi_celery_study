import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { taskApi } from '../api/taskApi';
import type { TaskHistoryRequest } from '../types';
import type { ChainExecutionResponseDto, PipelineStatusResponse } from '../types/pipeline';

// 파이프라인 이력 조회
export const useHistoryTasks = (params: TaskHistoryRequest) => {
  return useQuery<ChainExecutionResponseDto[]>({
    queryKey: ['pipeline-history', params],
    queryFn: () => taskApi.getHistoryTasks(params),
    refetchInterval: 10000, // 10초마다 자동 새로고침 (이력은 덜 자주 업데이트)
    staleTime: 5000, // 5초
  });
};

// 파이프라인 상태 확인
export const usePipelineStatus = (
  pipelineId: string,
  enabled = false,
  refetchInterval?: number
) => {
  return useQuery<PipelineStatusResponse>({
    queryKey: ['pipeline-status', pipelineId],
    queryFn: () => taskApi.getPipelineStatus(pipelineId),
    enabled: enabled && !!pipelineId,
    refetchInterval,
    staleTime: 1000, // 1초
  });
};

// 파이프라인 취소
export const useCancelPipeline = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: taskApi.cancelTasks,
    onSuccess: (_, pipelineId) => {
      console.log('파이프라인 취소 성공');
      // 관련된 쿼리들을 무효화
      queryClient.invalidateQueries({
        queryKey: ['pipeline-status', pipelineId],
      });
    },
    onError: (error) => {
      console.error('파이프라인 취소 실패:', error);
    },
  });
};


export const useExtractPdf = () => {
  return useMutation({
    mutationFn: taskApi.extractPdf,
    onSuccess: (data) => {
      console.log('PDF 추출 성공:', data);
    },
    onError: (error) => {
      console.error('PDF 추출 실패:', error);
    },
  });
};

// PDF 추출
export const useTestRunTask = () => {
  return useMutation({
    mutationFn: taskApi.testRunTask,
    
  });
};
