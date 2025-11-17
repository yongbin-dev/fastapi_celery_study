import React, { useState } from 'react';
import { ComparisonLayout } from '../components/comparison/ComparisonLayout';
import { ComparisonHeader } from '../components/comparison/ComparisonHeader';
import { ImagePanel } from '../components/comparison/ImagePanel';
import { ExecutionCompareInput } from '../components/comparison/ExecutionCompareInput';
import { SimilarityDisplay } from '../components/similarity/SimilarityDisplay';
import { useDualOcr } from '../hooks/useDualOcr';
import { ocrApi } from '../api/ocrApi';
import type { SimilarityAnalyzer } from '../types/comparison';
import type { CompareResponse } from '../api/ocrApi';

interface OcrComparisonPageProps {
  /**
   * 유사도 분석 함수 (외부에서 주입)
   */
  analyzeSimilarity: SimilarityAnalyzer;
}

const OcrComparisonPage: React.FC<OcrComparisonPageProps> = ({
  analyzeSimilarity,
}) => {
  const {
    state,
    handleFileSelect,
    handleExtract,
    handleAnalyzeSimilarity,
    handleClear,
    handleReset,
    canAnalyze,
  } = useDualOcr({ analyzeSimilarity });

  const [isComparing, setIsComparing] = useState(false);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(
    null
  );
  const [compareError, setCompareError] = useState<string | null>(null);

  const handleCompare = async (executionId1: string, executionId2: string) => {
    setIsComparing(true);
    setCompareError(null);
    setCompareResult(null);

    try {
      const result = await ocrApi.compareExecutions({
        execution_id1: executionId1,
        execution_id2: executionId2,
      });
      setCompareResult(result);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : '비교 요청 중 오류가 발생했습니다.';
      setCompareError(errorMessage);
      console.error('Comparison error:', error);
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div className="space-y-6">
      <ExecutionCompareInput
        onCompare={handleCompare}
        isLoading={isComparing}
      />

      {compareError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-medium">오류</p>
          <p className="text-red-600 text-sm mt-1">{compareError}</p>
        </div>
      )}

      {compareResult && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 font-medium mb-2">비교 완료</p>
          <div className="space-y-2 text-sm text-green-700">
            <p>Execution ID 1: {compareResult.execution_id1}</p>
            <p>Execution ID 2: {compareResult.execution_id2}</p>
            <p className="font-semibold">
              유사도 점수: {compareResult.comparison.similarity_score.toFixed(2)}%
            </p>
            {compareResult.comparison.differences.length > 0 && (
              <div className="mt-3">
                <p className="font-medium">차이점:</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  {compareResult.comparison.differences.map((diff, idx) => (
                    <li key={idx}>
                      라인 {diff.line}: "{diff.text1}" vs "{diff.text2}"
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="border-t pt-6">
        <ComparisonLayout
      header={
        <ComparisonHeader
          onReset={handleReset}
          hasData={!!(state.imageA.file || state.imageB.file)}
        />
      }
      imageA={
        <ImagePanel
          slot={state.imageA}
          onFileSelect={(file) => handleFileSelect('A', file)}
          onExtract={() => handleExtract('A')}
          onClear={() => handleClear('A')}
        />
      }
      imageB={
        <ImagePanel
          slot={state.imageB}
          onFileSelect={(file) => handleFileSelect('B', file)}
          onExtract={() => handleExtract('B')}
          onClear={() => handleClear('B')}
        />
      }
      similarity={
        <SimilarityDisplay
          result={state.similarityResult}
          isAnalyzing={state.isAnalyzing}
          canAnalyze={canAnalyze}
          onAnalyze={handleAnalyzeSimilarity}
        />
      }
        />
      </div>
    </div>
  );
};

export default OcrComparisonPage;
