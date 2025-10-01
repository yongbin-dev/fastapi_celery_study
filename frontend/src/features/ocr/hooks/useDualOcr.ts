import { useCallback, useState } from 'react';
import type {
  ComparisonState,
  ImageSlot,
  SimilarityAnalyzer,
} from '../types/comparison';
import { useExtractText } from './useOcr';

interface UseDualOcrOptions {
  /**
   * 유사도 분석 함수 (외부에서 주입)
   */
  analyzeSimilarity: SimilarityAnalyzer;
}

export const useDualOcr = (options: UseDualOcrOptions) => {
  const { analyzeSimilarity } = options;

  const [state, setState] = useState<ComparisonState>({
    imageA: createEmptySlot('A'),
    imageB: createEmptySlot('B'),
    similarityResult: null,
    isAnalyzing: false,
  });

  const mutationA = useExtractText();
  const mutationB = useExtractText();

  /**
   * 파일 선택 핸들러
   */
  const handleFileSelect = useCallback((slotId: 'A' | 'B', file: File) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      setState((prev) => ({
        ...prev,
        [slotId === 'A' ? 'imageA' : 'imageB']: {
          id: slotId,
          file,
          preview: reader.result as string,
          ocrResult: null,
          status: 'uploading' as const,
        },
        // 새 파일 선택 시 유사도 결과 초기화
        similarityResult: null,
      }));
    };
    reader.readAsDataURL(file);
  }, []);

  /**
   * OCR 추출 핸들러
   */
  const handleExtract = useCallback(
    (slotId: 'A' | 'B') => {
      const slot = slotId === 'A' ? state.imageA : state.imageB;
      const mutation = slotId === 'A' ? mutationA : mutationB;

      if (!slot.file) return;

      setState((prev) => ({
        ...prev,
        [slotId === 'A' ? 'imageA' : 'imageB']: {
          ...slot,
          status: 'extracting' as const,
        },
        // OCR 재실행 시 유사도 결과 초기화
        similarityResult: null,
      }));

      mutation.mutate(
        { image_file: slot.file },
        {
          onSuccess: (data) => {
            setState((prev) => ({
              ...prev,
              [slotId === 'A' ? 'imageA' : 'imageB']: {
                ...slot,
                ocrResult: data,
                status: 'complete' as const,
              },
            }));
          },
          onError: (error) => {
            setState((prev) => ({
              ...prev,
              [slotId === 'A' ? 'imageA' : 'imageB']: {
                ...slot,
                status: 'error' as const,
                error: error.message,
              },
            }));
          },
        }
      );
    },
    [state, mutationA, mutationB]
  );

  /**
   * 유사도 분석 핸들러 (외부 함수 호출)
   */
  const handleAnalyzeSimilarity = useCallback(async () => {
    if (!state.imageA.ocrResult || !state.imageB.ocrResult) return;

    setState((prev) => ({ ...prev, isAnalyzing: true }));

    try {
      const result = await analyzeSimilarity(
        state.imageA.ocrResult,
        state.imageB.ocrResult
      );

      setState((prev) => ({
        ...prev,
        similarityResult: result,
        isAnalyzing: false,
      }));
    } catch (error) {
      console.error('Similarity analysis failed:', error);
      setState((prev) => ({ ...prev, isAnalyzing: false }));
    }
  }, [state.imageA.ocrResult, state.imageB.ocrResult, analyzeSimilarity]);

  /**
   * 슬롯 초기화
   */
  const handleClear = useCallback(
    (slotId: 'A' | 'B') => {
      setState((prev) => ({
        ...prev,
        [slotId === 'A' ? 'imageA' : 'imageB']: createEmptySlot(slotId),
        similarityResult: null,
      }));

      // mutation 초기화
      if (slotId === 'A') {
        mutationA.reset();
      } else {
        mutationB.reset();
      }
    },
    [mutationA, mutationB]
  );

  /**
   * 전체 초기화
   */
  const handleReset = useCallback(() => {
    setState({
      imageA: createEmptySlot('A'),
      imageB: createEmptySlot('B'),
      similarityResult: null,
      isAnalyzing: false,
    });
    mutationA.reset();
    mutationB.reset();
  }, [mutationA, mutationB]);

  // 유사도 분석 가능 여부
  const canAnalyze = !!(
    state.imageA.ocrResult &&
    state.imageB.ocrResult &&
    !state.isAnalyzing
  );

  // 양쪽 OCR 진행 상태
  const isExtracting =
    state.imageA.status === 'extracting' ||
    state.imageB.status === 'extracting';

  return {
    state,
    handleFileSelect,
    handleExtract,
    handleAnalyzeSimilarity,
    handleClear,
    handleReset,
    canAnalyze,
    isExtracting,
  };
};

/**
 * 빈 슬롯 생성
 */
const createEmptySlot = (id: 'A' | 'B'): ImageSlot => ({
  id,
  file: null,
  preview: null,
  ocrResult: null,
  status: 'idle',
});
