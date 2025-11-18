import React from 'react';
import { ComparisonLayout } from '../components/comparison/ComparisonLayout';
import { ComparisonHeader } from '../components/comparison/ComparisonHeader';
import { ImagePanel } from '../components/comparison/ImagePanel';
import { ExecutionCompareInput } from '../components/comparison/ExecutionCompareInput';
import { SimilarityDisplay } from '../components/similarity/SimilarityDisplay';
import { useDualOcr, useCompareExecutions } from '../hooks';
import type { SimilarityAnalyzer } from '../types/comparison';

interface MetricCardProps {
  label: string;
  value: number | null;
  distance?: number;
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, distance }) => {
  const displayValue = value !== null ? (value * 100).toFixed(1) : 'N/A';
  const hasValue = value !== null;

  return (
    <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
      <p className="text-xs text-gray-600 mb-1">{label}</p>
      <p className={`text-lg font-semibold ${hasValue ? 'text-gray-900' : 'text-gray-400'}`}>
        {hasValue ? `${displayValue}%` : displayValue}
      </p>
      {distance !== undefined && (
        <p className="text-xs text-gray-500 mt-1">거리: {distance}</p>
      )}
    </div>
  );
};

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

  const {
    mutate: compareExecutions,
    isPending: isComparing,
    data: compareResult,
    error: compareError,
  } = useCompareExecutions({
    onSuccess: (data) => {
      console.log('비교 완료:', data);
    },
    onError: (error) => {
      console.error('Comparison error:', error);
    },
  });

  const handleCompare = (executionId1: string, executionId2: string) => {
    compareExecutions({
      execution_id1: executionId1,
      execution_id2: executionId2,
    });
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
          <p className="text-red-600 text-sm mt-1">{compareError.message}</p>
        </div>
      )}

      {compareResult && (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          {/* 헤더 */}
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-4">
            <h2 className="text-white font-semibold text-lg">비교 결과</h2>
            <p className="text-blue-100 text-sm mt-1">
              Execution #{compareResult.execution_id1} vs #{compareResult.execution_id2}
            </p>
          </div>

          <div className="p-6 space-y-6">
            {/* 전체 유사도 점수 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
                <p className="text-xs text-purple-600 font-medium mb-1">전체 유사도</p>
                <p className="text-2xl font-bold text-purple-900">
                  {(compareResult.overall_similarity * 100).toFixed(1)}%
                </p>
              </div>
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
                <p className="text-xs text-blue-600 font-medium mb-1">문자열 유사도</p>
                <p className="text-2xl font-bold text-blue-900">
                  {(compareResult.string_similarity * 100).toFixed(1)}%
                </p>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
                <p className="text-xs text-green-600 font-medium mb-1">토큰 유사도</p>
                <p className="text-2xl font-bold text-green-900">
                  {(compareResult.token_similarity * 100).toFixed(1)}%
                </p>
              </div>
              <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg p-4 border border-amber-200">
                <p className="text-xs text-amber-600 font-medium mb-1">의미 유사도</p>
                <p className="text-2xl font-bold text-amber-900">
                  {compareResult.semantic_similarity !== null
                    ? `${(compareResult.semantic_similarity * 100).toFixed(1)}%`
                    : 'N/A'}
                </p>
              </div>
            </div>

            {/* 상세 메트릭 */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                <span className="w-1 h-4 bg-blue-500 rounded mr-2"></span>
                상세 메트릭
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                <MetricCard
                  label="Levenshtein 유사도"
                  value={compareResult.metrics.levenshtein_similarity}
                  distance={compareResult.metrics.levenshtein_distance}
                />
                <MetricCard
                  label="Jaro-Winkler"
                  value={compareResult.metrics.jaro_winkler}
                />
                <MetricCard
                  label="Sequence Matcher"
                  value={compareResult.metrics.sequence_matcher}
                />
                <MetricCard
                  label="Jaccard Index"
                  value={compareResult.metrics.jaccard_index}
                />
                <MetricCard
                  label="Cosine 유사도"
                  value={compareResult.metrics.cosine_similarity}
                />
                <MetricCard
                  label="의미적 유사도"
                  value={compareResult.metrics.semantic_similarity}
                />
              </div>
            </div>

            {/* 매칭된 텍스트 */}
            {compareResult.matched_texts.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <span className="w-1 h-4 bg-green-500 rounded mr-2"></span>
                  매칭된 텍스트 ({compareResult.matched_texts.length}건)
                </h3>
                <div className="bg-green-50 rounded-lg p-4 border border-green-200 max-h-60 overflow-y-auto">
                  <ul className="space-y-2">
                    {compareResult.matched_texts.map((match, idx) => (
                      <li key={idx} className="text-sm text-green-800">
                        <span className="font-mono bg-green-100 px-2 py-1 rounded">
                          L{match.line1}/{match.line2}
                        </span>
                        <span className="ml-2">{match.text}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* 차이점 */}
            {compareResult.differences.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <span className="w-1 h-4 bg-red-500 rounded mr-2"></span>
                  차이점 ({compareResult.differences.length}건)
                </h3>
                <div className="bg-red-50 rounded-lg p-4 border border-red-200 max-h-60 overflow-y-auto">
                  <ul className="space-y-3">
                    {compareResult.differences.map((diff, idx) => (
                      <li key={idx} className="text-sm">
                        <div className="font-medium text-red-700 mb-1">
                          라인 {diff.line}
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <div className="bg-red-100 rounded p-2">
                            <p className="text-xs text-red-600 font-medium mb-1">실행 1</p>
                            <p className="text-red-800 font-mono text-xs break-all">
                              "{diff.text1}"
                            </p>
                          </div>
                          <div className="bg-red-100 rounded p-2">
                            <p className="text-xs text-red-600 font-medium mb-1">실행 2</p>
                            <p className="text-red-800 font-mono text-xs break-all">
                              "{diff.text2}"
                            </p>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* 차이점이 없을 때 */}
            {compareResult.differences.length === 0 && (
              <div className="bg-green-50 rounded-lg p-4 border border-green-200 text-center">
                <p className="text-green-800 font-medium">
                  ✓ 두 실행 결과가 완전히 일치합니다!
                </p>
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
