import React from 'react';
import { SimilarityScore } from './SimilarityScore';
import { MetricsGrid } from './MetricsGrid';
import { DifferenceList } from './DifferenceList';
import { AnalyzeButton } from './AnalyzeButton';
import type { SimilarityResult } from '../../types/comparison';

interface SimilarityDisplayProps {
  result: SimilarityResult | null;
  isAnalyzing: boolean;
  canAnalyze: boolean;
  onAnalyze: () => void;
}

export const SimilarityDisplay: React.FC<SimilarityDisplayProps> = ({
  result,
  isAnalyzing,
  canAnalyze,
  onAnalyze,
}) => {
  return (
    <div className="p-6 space-y-6">
      {/* 헤더 */}
      <h3 className="text-lg font-semibold text-gray-800">유사도 분석</h3>

      {/* 분석 전 상태 */}
      {!result && !isAnalyzing && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="w-16 h-16 mb-4 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-3xl">🔍</span>
          </div>
          <p className="text-gray-600 mb-6">
            양쪽 이미지에서 텍스트를 추출한 후
            <br />
            유사도를 분석할 수 있습니다
          </p>
          <AnalyzeButton
            onClick={onAnalyze}
            disabled={!canAnalyze}
            isAnalyzing={false}
          />
        </div>
      )}

      {/* 분석 중 */}
      {isAnalyzing && (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-gray-600">유사도를 분석하고 있습니다...</p>
        </div>
      )}

      {/* 분석 결과 */}
      {result && !isAnalyzing && (
        <>
          <SimilarityScore score={result.overallScore} />
          <MetricsGrid metrics={result.metrics} />

          {result.differences.length > 0 && (
            <DifferenceList differences={result.differences} />
          )}

          <div className="flex gap-2">
            <AnalyzeButton
              onClick={onAnalyze}
              disabled={!canAnalyze}
              isAnalyzing={false}
              className="flex-1"
            />
            <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
              결과 내보내기
            </button>
          </div>
        </>
      )}
    </div>
  );
};
