import React from 'react';

interface AnalyzeButtonProps {
  onClick: () => void;
  disabled: boolean;
  isAnalyzing: boolean;
  className?: string;
}

export const AnalyzeButton: React.FC<AnalyzeButtonProps> = ({
  onClick,
  disabled,
  isAnalyzing,
  className = '',
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled || isAnalyzing}
      className={`
        px-6 py-3 bg-blue-600 text-white rounded-lg font-medium
        hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
        transition-colors
        ${className}
      `}
    >
      {isAnalyzing ? (
        <span className="flex items-center justify-center gap-2">
          <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          분석 중...
        </span>
      ) : (
        '유사도 분석'
      )}
    </button>
  );
};
