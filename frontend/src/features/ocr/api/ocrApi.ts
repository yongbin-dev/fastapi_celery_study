import { api } from '@/shared/utils/api';
import type { OcrResponse } from '../types/ocr';

interface OcrRequest {
  image_file: File;
  language?: string;
  confidence_threshold?: number;
  use_angle_cls?: boolean;
}

interface CompareRequest {
  execution_id1: string;
  execution_id2: string;
}

interface CompareResponse {
  execution_id1: string;
  execution_id2: string;
  result1: OcrResponse;
  result2: OcrResponse;
  comparison: {
    similarity_score: number;
    differences: Array<{
      line: number;
      text1: string;
      text2: string;
    }>;
  };
}

export const ocrApi = {
  extractTextSync: async (data: OcrRequest): Promise<OcrResponse> => {
    const formData = new FormData();
    formData.append('image_file', data.image_file);
    if (data.language) {
      formData.append('language', data.language);
    }
    if (data.confidence_threshold) {
      formData.append(
        'confidence_threshold',
        data.confidence_threshold.toString()
      );
    }
    if (data.use_angle_cls !== undefined) {
      formData.append('use_angle_cls', data.use_angle_cls.toString());
    }

    const response = await api.post<OcrResponse>(
      '/ocr/extract/sync',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 60 seconds
      }
    );
    return response.data;
  },

  extractImageSync: async (image_path: string): Promise<OcrResponse> => {
    const response = await api.get<OcrResponse>(
      `/ocr/extract/sync/${image_path}`
    );
    return response.data;
  },

  getOcrResults: async (): Promise<OcrResponse[]> => {
    const response = await api.get<OcrResponse[]>('/ocr/results');
    return response.data;
  },

  compareExecutions: async (data: CompareRequest): Promise<CompareResponse> => {
    const response = await api.post<CompareResponse>('/compare', data);
    return response.data;
  },
};

export type { CompareRequest, CompareResponse };
