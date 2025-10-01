import React from 'react';

interface ComparisonHeaderProps {
  onReset: () => void;
  hasData: boolean;
}

export const ComparisonHeader: React.FC<ComparisonHeaderProps> = ({
  onReset,
  hasData,
}) => {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">
          OCR 이미지 비교 분석
        </h1>
        <p className="text-gray-500 mt-1">
          2개의 이미지를 업로드하여 텍스트 유사도를 비교하세요
        </p>
      </div>
      {hasData && (
        <button
          onClick={onReset}
          className="px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors font-medium"
        >
          전체 초기화
        </button>
      )}
    </div>
  );
};
