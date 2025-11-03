import { api, ml_api } from '@/shared/utils/api';
import type { TaskHistoryRequest } from '../types';
import { type PipelineStatusResponse, type ChainExecutionResponseDto } from '../types/pipeline';

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
    const url = `/pipeline/history?${queryString ? `${queryString}` : ''}`;

    const response = await api.get<ChainExecutionResponseDto[]>(url);
    return response.data;
  },

  // PDF 추출
  extractPdf: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('pdf_file', file);

    const response = await api.post<any>('/pipeline/extract/pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },


  // PDF 추출
  testRunTask: async (): Promise<any> => {
    const response = await ml_api.get<any>('/ocr/test-async',  {
      headers: {
      },
    });
    return response.data;
  },

  // 파이프라인 상태 확인
  getPipelineStatus: async (
    pipelineId: string
  ): Promise<PipelineStatusResponse> => {
    const response = await ml_api.get<PipelineStatusResponse>(
      `/ocr/result/${pipelineId}`
    );
    return response.data;
  },


  cancelTasks: async (pipelineId: string): Promise<void> => {
    await ml_api.get(`/ocr/cancel/${pipelineId}`);
  },

};
