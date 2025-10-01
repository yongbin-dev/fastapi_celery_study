import React from 'react';
import type { TextDifference } from '../../types/comparison';

interface DifferenceListProps {
  differences: TextDifference[];
}

export const DifferenceList: React.FC<DifferenceListProps> = ({
  differences,
}) => {
  if (differences.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold text-gray-700">
        차이점 ({differences.length}개)
      </h4>
      <div className="max-h-60 overflow-y-auto space-y-2">
        {differences.map((diff, index) => (
          <DifferenceItem key={index} difference={diff} />
        ))}
      </div>
    </div>
  );
};

const DifferenceItem: React.FC<{ difference: TextDifference }> = ({
  difference,
}) => {
  const getDiffTypeColor = (type: TextDifference['diffType']) => {
    switch (type) {
      case 'exact':
        return 'bg-green-50 border-green-200';
      case 'partial':
        return 'bg-yellow-50 border-yellow-200';
      case 'missing-a':
      case 'missing-b':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div
      className={`p-3 rounded-lg border ${getDiffTypeColor(difference.diffType)}`}
    >
      <div className="flex justify-between items-start mb-2">
        <span className="text-xs font-semibold text-gray-600">
          Line {difference.lineNumber}
        </span>
        <span className="text-xs text-gray-500">
          {(difference.similarity * 100).toFixed(0)}% 유사
        </span>
      </div>
      <div className="space-y-1 text-sm">
        <div>
          <span className="text-xs font-semibold text-gray-500">A: </span>
          <span className="text-gray-700">{difference.textA || '(없음)'}</span>
        </div>
        <div>
          <span className="text-xs font-semibold text-gray-500">B: </span>
          <span className="text-gray-700">{difference.textB || '(없음)'}</span>
        </div>
      </div>
    </div>
  );
};
