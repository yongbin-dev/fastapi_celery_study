import type { OcrResponse } from './ocr';

/**
 * 이미지 슬롯 (A 또는 B)
 */
export interface ImageSlot {
  id: 'A' | 'B';
  file: File | null;
  preview: string | null;
  ocrResult: OcrResponse | null;
  status: 'idle' | 'uploading' | 'extracting' | 'complete' | 'error';
  error?: string;
}

/**
 * 유사도 결과 (외부에서 계산된 결과를 받음)
 */
export interface SimilarityResult {
  overallScore: number; // 0-100
  metrics: SimilarityMetrics;
  differences: TextDifference[];
  matchedPairs: MatchedPair[];
}

/**
 * 유사도 메트릭
 */
export interface SimilarityMetrics {
  exactMatches: number;
  partialMatches: number;
  missingInA: number;
  missingInB: number;
  characterSimilarity: number;
  wordSimilarity: number;
  lineSimilarity: number;
}

/**
 * 텍스트 차이점
 */
export interface TextDifference {
  lineNumber: number;
  textA: string;
  textB: string;
  similarity: number;
  diffType: 'missing-a' | 'missing-b' | 'partial' | 'exact';
}

/**
 * 매칭된 텍스트 쌍
 */
export interface MatchedPair {
  indexA: number;
  indexB: number;
  textA: string;
  textB: string;
  similarity: number;
}

/**
 * 전체 비교 상태
 */
export interface ComparisonState {
  imageA: ImageSlot;
  imageB: ImageSlot;
  similarityResult: SimilarityResult | null;
  isAnalyzing: boolean;
}

/**
 * 유사도 분석 함수 타입 (외부에서 주입)
 */
export type SimilarityAnalyzer = (
  resultA: OcrResponse,
  resultB: OcrResponse
) => Promise<SimilarityResult>;
