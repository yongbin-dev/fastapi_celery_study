import { api } from '@/shared/utils/api';
import type {
  ModelTestRequest,
  ModelTestResponse,
  TaskHistoryRequest,
} from '../types';
import type { ChainExecutionResponseDto } from '../types/pipeline';

export const taskApi = {
  getHistoryTasks: async (
    params: TaskHistoryRequest
  ): Promise<ChainExecutionResponseDto[]> => {
    // 빈 문자열인 매개변수들을 제거하고 쿼리 스트링 생성
    const searchParams = new URLSearchParams();

    if (params.hours) searchParams.append('hours', params.hours.toString());
    if (params.status && params.status.trim())
      searchParams.append('status', params.status);
    if (params.task_name && params.task_name.trim())
      searchParams.append('task_name', params.task_name);
    if (params.limit) searchParams.append('limit', params.limit.toString());

    const queryString = searchParams.toString();
    const url = `/tasks/history?${queryString ? `${queryString}` : ''}`;

    const response = await api.get<ChainExecutionResponseDto[]>(url);
    return response.data;
  },

  // 모델 테스트 (이미지 두개 업로드)
  createModelTest: async (
    data: ModelTestRequest
  ): Promise<ModelTestResponse> => {
    const formData = new FormData();
    formData.append('image1', data.image1);
    formData.append('image2', data.image2);

    const response = await api.post<ModelTestResponse>(
      '/tasks/model-test',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // 파이프라인 시작
  startPipeline: async (data: {
    text: string;
    options: { model: string };
  }): Promise<{ pipeline_id: string }> => {
    const response = await api.post<{ pipeline_id: string }>(
      '/tasks/ai-pipeline',
      data
    );
    return response.data;
  },

  // 파이프라인 상태 확인
  getPipelineStatus: async (
    pipelineId: string
  ): Promise<ChainExecutionResponseDto> => {
    const response = await api.get<ChainExecutionResponseDto>(
      `/tasks/ai-pipeline/${pipelineId}/tasks`
    );
    return response.data;
  },

  // 파이프라인 취소
  cancelPipeline: async (pipelineId: string): Promise<void> => {
    await api.delete(`/tasks/ai-pipeline/${pipelineId}/cancel`);
  },
};
