import type { OcrResponse } from '../types/ocr';
import type { SimilarityResult } from '../types/comparison';

/**
 * 두 OCR 결과의 유사도를 분석
 *
 * @param resultA - 이미지 A의 OCR 결과
 * @param resultB - 이미지 B의 OCR 결과
 * @returns 유사도 분석 결과
 *
 * @example
 * ```typescript
 * const result = await analyzeSimilarity(ocrA, ocrB);
 * console.log(`유사도: ${result.overallScore}%`);
 * ```
 */
export const analyzeSimilarity = async (
  resultA: OcrResponse,
  resultB: OcrResponse
): Promise<SimilarityResult> => {
  // TODO: 유사도 계산 로직 구현
  // 아래는 임시 구현 (테스트용)

  // 임시 데이터 반환
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        overallScore: 85,
        metrics: {
          exactMatches: 10,
          partialMatches: 2,
          missingInA: 1,
          missingInB: 1,
          characterSimilarity: 87,
          wordSimilarity: 82,
          lineSimilarity: 85,
        },
        differences: [
          {
            lineNumber: 3,
            textA: 'Page 1 of 3',
            textB: 'Page 1 of 2',
            similarity: 0.95,
            diffType: 'partial',
          },
        ],
        matchedPairs: [],
      });
    }, 500);
  });
};

/**
 * 레벤슈타인 거리 기반 문자열 유사도 계산
 *
 * @param str1 - 첫 번째 문자열
 * @param str2 - 두 번째 문자열
 * @returns 유사도 (0-1)
 *
 * @example
 * ```typescript
 * const similarity = calculateStringSimilarity('hello', 'hallo');
 * console.log(similarity); // 0.8
 * ```
 */
export const calculateStringSimilarity = (
  str1: string,
  str2: string
): number => {
  // TODO: 레벤슈타인 거리 알고리즘 구현
  const longer = str1.length > str2.length ? str1 : str2;
  const shorter = str1.length > str2.length ? str2 : str1;

  if (longer.length === 0) return 1.0;

  const editDistance = levenshteinDistance(longer, shorter);
  return (longer.length - editDistance) / longer.length;
};

/**
 * 레벤슈타인 거리 계산
 *
 * @param str1 - 첫 번째 문자열
 * @param str2 - 두 번째 문자열
 * @returns 편집 거리
 */
const levenshteinDistance = (str1: string, str2: string): number => {
  // TODO: 레벤슈타인 거리 알고리즘 구현
  const matrix: number[][] = [];

  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }

  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j;
  }

  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }

  return matrix[str2.length][str1.length];
};
