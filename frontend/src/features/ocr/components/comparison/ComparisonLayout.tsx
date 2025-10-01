import React from 'react';

interface ComparisonLayoutProps {
  imageA: React.ReactNode;
  imageB: React.ReactNode;
  similarity: React.ReactNode;
  header?: React.ReactNode;
}

export const ComparisonLayout: React.FC<ComparisonLayoutProps> = ({
  imageA,
  imageB,
  similarity,
  header,
}) => {
  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6 lg:p-8">
      {/* Header */}
      {header && <div className="mb-6">{header}</div>}

      {/* 데스크톱: 3-column, 태블릿/모바일: 스택 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Image A Panel */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {imageA}
        </div>

        {/* Similarity Panel */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {similarity}
        </div>

        {/* Image B Panel */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {imageB}
        </div>
      </div>
    </div>
  );
};
