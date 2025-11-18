import { useMutation, useQuery } from '@tanstack/react-query';
import { ocrApi } from '../api/ocrApi';

import type { CompareResponse } from '../api/ocrApi';
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

export const useExtractImage = (
  options: { onSuccess?: (data: OcrResponse) => void } = {}
) => {
  return useMutation({
    mutationFn: ocrApi.extractImageSync,
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

export const useCompareExecutions = (
  options: { onSuccess?: (data: CompareResponse) => void; onError?: (error: Error) => void } = {}
) => {
  return useMutation({
    mutationFn: ocrApi.compareExecutions,
    onSuccess: (data) => {
      options.onSuccess?.(data);
    },
    onError: (error: Error) => {
      options.onError?.(error);
    },
  });
};
