import React from 'react';
import type { SimilarityMetrics } from '../../types/comparison';

interface MetricsGridProps {
  metrics: SimilarityMetrics;
}

export const MetricsGrid: React.FC<MetricsGridProps> = ({ metrics }) => {
  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-700 mb-3">상세 메트릭</h4>
      <div className="grid grid-cols-2 gap-3">
        <MetricCard label="완전 일치" value={metrics.exactMatches} icon="✅" />
        <MetricCard label="부분 일치" value={metrics.partialMatches} icon="⚠️" />
        <MetricCard label="A 누락" value={metrics.missingInA} icon="📭" />
        <MetricCard label="B 누락" value={metrics.missingInB} icon="📭" />
      </div>

      <div className="mt-4 space-y-2">
        <SimilarityBar
          label="문자 유사도"
          value={metrics.characterSimilarity}
        />
        <SimilarityBar label="단어 유사도" value={metrics.wordSimilarity} />
        <SimilarityBar label="라인 유사도" value={metrics.lineSimilarity} />
      </div>
    </div>
  );
};

const MetricCard = ({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon: string;
}) => (
  <div className="p-3 bg-gray-50 rounded-lg">
    <div className="flex items-center gap-2 mb-1">
      <span>{icon}</span>
      <span className="text-xs text-gray-600">{label}</span>
    </div>
    <p className="text-xl font-semibold text-gray-800">{value}</p>
  </div>
);

const SimilarityBar = ({
  label,
  value,
}: {
  label: string;
  value: number;
}) => (
  <div>
    <div className="flex justify-between text-xs text-gray-600 mb-1">
      <span>{label}</span>
      <span>{value}%</span>
    </div>
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className="h-2 bg-blue-500 rounded-full transition-all"
        style={{ width: `${value}%` }}
      />
    </div>
  </div>
);
