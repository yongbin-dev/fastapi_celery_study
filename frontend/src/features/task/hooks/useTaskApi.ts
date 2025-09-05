import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { taskApi } from '../api/taskApi';
import type { PipelineStatusResponse, TaskHistoryRequest } from '../types';

// 예제 태스크 생성
// export const useCreateExampleTask = () => {
//   const queryClient = useQueryClient();

//   return useMutation({
//     mutationFn: taskApi.createExampleTask,
//     onSuccess: (data) => {
//       console.log('예제 태스크 생성 성공:', data.task_id);
//       queryClient.invalidateQueries({ queryKey: ['active-tasks'] });
//     },
//     onError: (error) => {
//       console.error('예제 태스크 생성 실패:', error);
//     },
//   });
// };

// // 이메일 태스크 생성
// export const useCreateEmailTask = () => {
//   const queryClient = useQueryClient();

//   return useMutation({
//     mutationFn: taskApi.createEmailTask,
//     onSuccess: (data) => {
//       console.log('이메일 태스크 생성 성공:', data.task_id);
//       queryClient.invalidateQueries({ queryKey: ['active-tasks'] });
//     },
//     onError: (error) => {
//       console.error('이메일 태스크 생성 실패:', error);
//     },
//   });
// };

// 긴 태스크 생성
// export const useCreateLongTask = () => {
//   const queryClient = useQueryClient();

//   return useMutation({
//     mutationFn: taskApi.createLongTask,
//     onSuccess: (data) => {
//       console.log('긴 태스크 생성 성공:', data.task_id);
//       queryClient.invalidateQueries({ queryKey: ['active-tasks'] });
//     },
//     onError: (error) => {
//       console.error('긴 태스크 생성 실패:', error);
//     },
//   });
// };

// 태스크 취소
// export const useCancelTask = () => {
//   const queryClient = useQueryClient();

//   return useMutation({
//     mutationFn: (taskId: string) => taskApi.cancelTask(taskId),
//     onSuccess: (data) => {
//       console.log('태스크 취소 성공:', data.task_id);
//       queryClient.invalidateQueries({ queryKey: ['active-tasks'] });
//       queryClient.invalidateQueries({ queryKey: ['task-status'] });
//     },
//     onError: (error) => {
//       console.error('태스크 취소 실패:', error);
//     },
//   });
// };

export const useCreateAITask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: taskApi.createAITask,
    onSuccess: (data) => {
      console.log('AI 태스크 생성 성공:', data.task_id);
      queryClient.invalidateQueries({ queryKey: ['active-tasks'] });
    },
    onError: (error) => {
      console.error('AI 태스크 생성 실패:', error);
    },
  });
};

// 활성 태스크 목록 조회
export const useActiveTasks = (enabled = true) => {
  return useQuery({
    queryKey: ['active-tasks'],
    queryFn: taskApi.getActiveTasks,
    enabled,
    refetchInterval: 5000, // 5초마다 자동 새로고침
    staleTime: 2000, // 2초
  });
};

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
