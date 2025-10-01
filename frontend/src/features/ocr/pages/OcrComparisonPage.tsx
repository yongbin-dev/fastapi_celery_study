import React from 'react';
import { ComparisonLayout } from '../components/comparison/ComparisonLayout';
import { ComparisonHeader } from '../components/comparison/ComparisonHeader';
import { ImagePanel } from '../components/comparison/ImagePanel';
import { SimilarityDisplay } from '../components/similarity/SimilarityDisplay';
import { useDualOcr } from '../hooks/useDualOcr';
import type { SimilarityAnalyzer } from '../types/comparison';

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

  return (
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
  );
};

export default OcrComparisonPage;
