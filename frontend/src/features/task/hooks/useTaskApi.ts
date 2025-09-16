import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { taskApi } from '../api/taskApi';
import type { PipelineStatusResponse, TaskHistoryRequest } from '../types';


// 파이프라인 이력 조회
export const useHistoryTasks = (params: TaskHistoryRequest) => {
  return useQuery<PipelineStatusResponse[]>({
    queryKey: ['pipeline-history', params],
    queryFn: () => taskApi.getHistoryTasks(params),
    refetchInterval: 10000, // 10초마다 자동 새로고침 (이력은 덜 자주 업데이트)
    staleTime: 5000, // 5초
  });
};

export const useImageTask = () => {
  return useMutation({
    mutationFn: taskApi.createModelTest,
    onSuccess: (data) => {
      console.log('AI 태스크 생성 성공:', data.task_id);
    },
    onError: (error) => {
      console.error('AI 태스크 생성 실패:', error);
    },
  });
};

// 파이프라인 시작
export const useStartPipeline = () => {
  return useMutation({
    mutationFn: taskApi.startPipeline,
    onSuccess: (data) => {
      console.log('파이프라인 시작 성공:', data.pipeline_id);
    },
    onError: (error) => {
      console.error('파이프라인 시작 실패:', error);
    },
  });
};

// 파이프라인 상태 확인
export const usePipelineStatus = (
  pipelineId: string,
  enabled = false,
  refetchInterval?: number
) => {
  return useQuery({
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
    mutationFn: taskApi.cancelPipeline,
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
