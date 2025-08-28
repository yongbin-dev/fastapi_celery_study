import { api } from '@/shared/utils/api';
import type {
  ActiveTasksResponse,
  AITaskRequest,
  EmailTaskRequest,
  LongTaskRequest,
  TaskRequest,
  TaskResponse,
  TaskHistoryRequest,
  TaskHistoryResponse,
  ModelTestRequest,
  ModelTestResponse,
} from '../types';

export const taskApi = {
  // 예제 태스크 생성
  createExampleTask: async (data: TaskRequest): Promise<TaskResponse> => {
    const response = await api.post<TaskResponse>(
      '/api/v1/tasks/example',
      data
    );
    return response.data;
  },

  // AI 처리 태스크 생성
  createAITask: async (data: AITaskRequest): Promise<TaskResponse> => {
    const response = await api.post<TaskResponse>(
      '/api/v1/tasks/ai-processing',
      data
    );
    return response.data;
  },

  // 이메일 발송 태스크 생성
  createEmailTask: async (data: EmailTaskRequest): Promise<TaskResponse> => {
    const response = await api.post<TaskResponse>(
      '/api/v1/tasks/send-email',
      data
    );
    return response.data;
  },

  // 긴 시간 소요 태스크 생성
  createLongTask: async (data: LongTaskRequest): Promise<TaskResponse> => {
    const response = await api.post<TaskResponse>(
      '/api/v1/tasks/long-running',
      data
    );
    return response.data;
  },

  // 태스크 취소
  cancelTask: async (taskId: string): Promise<TaskResponse> => {
    const response = await api.delete<TaskResponse>(
      `/api/v1/tasks/cancel/${taskId}`
    );
    return response.data;
  },

  // 활성 태스크 목록 조회
  getActiveTasks: async (): Promise<ActiveTasksResponse> => {
    const response = await api.get<ActiveTasksResponse>('/api/v1/tasks/list');
    return response.data;
  },

  getHistoryTasks: async (params: TaskHistoryRequest): Promise<TaskHistoryResponse> => {
    // 빈 문자열인 매개변수들을 제거하고 쿼리 스트링 생성
    const searchParams = new URLSearchParams();
    
    if (params.hours) searchParams.append('hours', params.hours.toString());
    if (params.status && params.status.trim()) searchParams.append('status', params.status);
    if (params.task_name && params.task_name.trim()) searchParams.append('task_name', params.task_name);
    if (params.limit) searchParams.append('limit', params.limit.toString());

    const queryString = searchParams.toString();
    const url = `/api/v1/tasks/history${queryString ? `?${queryString}` : ''}`;
    
    const response = await api.get<TaskHistoryResponse>(url);
    return response.data;
  },

  // 모델 테스트 (이미지 두개 업로드)
  createModelTest: async (data: ModelTestRequest): Promise<ModelTestResponse> => {
    const formData = new FormData();
    formData.append('image1', data.image1);
    formData.append('image2', data.image2);
    
    const response = await api.post<ModelTestResponse>(
      '/api/v1/tasks/model-test',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },
};
