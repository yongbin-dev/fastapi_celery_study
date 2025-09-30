import { api } from '@/shared/utils/api';
import type { OcrResponse } from '../types/ocr';

interface OcrRequest {
  image_file: File;
  language?: string;
  confidence_threshold?: number;
  use_angle_cls?: boolean;
}

export const ocrApi = {
  extractTextSync: async (data: OcrRequest): Promise<OcrResponse> => {
    const formData = new FormData();
    formData.append('image_file', data.image_file);
    if (data.language) {
      formData.append('language', data.language);
    };
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
};
