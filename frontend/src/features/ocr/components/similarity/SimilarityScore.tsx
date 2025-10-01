import React from 'react';

interface SimilarityScoreProps {
  score: number; // 0-100
}

export const SimilarityScore: React.FC<SimilarityScoreProps> = ({ score }) => {
  const getColor = (score: number) => {
    if (score >= 80) return { text: 'text-green-600', bg: 'bg-green-500' };
    if (score >= 60) return { text: 'text-yellow-600', bg: 'bg-yellow-500' };
    return { text: 'text-red-600', bg: 'bg-red-500' };
  };

  const colors = getColor(score);

  return (
    <div className="text-center">
      <p className="text-sm text-gray-600 mb-2">전체 유사도</p>
      <div className={`text-5xl font-bold mb-4 ${colors.text}`}>{score}%</div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className={`h-3 rounded-full transition-all ${colors.bg}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
};
