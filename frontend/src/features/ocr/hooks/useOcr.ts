import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ocrApi } from '../api/ocrApi';

import type { OcrResponse } from '../types/ocr';

export const useExtractText = (
  options: { onSuccess?: (data: OcrResponse) => void } = {}
) => {
  return useMutation({
    mutationFn: ocrApi.extractTextSync,
    onSuccess: (data) => {
      options.onSuccess?.(data);
    },
  });
};

export const useOcrResults = () => {
  return useQuery({
    queryKey: ['ocrResults'],
    queryFn: ocrApi.getOcrResults,
  });
};
