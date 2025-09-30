import { useMutation } from '@tanstack/react-query';
import { ocrApi } from '../api/ocrApi';

export const useExtractText = () => {
  return useMutation({
    mutationFn: ocrApi.extractTextSync,
  });
};