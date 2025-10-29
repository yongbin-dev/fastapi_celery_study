import React from 'react';
import type { OcrResponse } from '../../types/ocr';

interface OcrResultDisplayProps {
  result: OcrResponse;
}

export const OcrResultDisplay: React.FC<OcrResultDisplayProps> = ({ result }) => {
  return (
    <div className="space-y-4">
      {/* 통계 */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-blue-50 rounded-lg">
          <p className="text-xs text-gray-600">텍스트 박스</p>
          <p className="text-lg font-semibold text-blue-600">
            {result.text_boxes.length}개
          </p>
        </div>
        <div className="p-3 bg-green-50 rounded-lg">
          <p className="text-xs text-gray-600">평균 신뢰도</p>
          <p className="text-lg font-semibold text-green-600">
            {(result.average_confidence * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* 텍스트 박스 목록 (축약) */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-2">
          인식된 텍스트 ({result.text_boxes.length}개)
        </h4>
        <div className="h-full space-y-2">
          {result.text_boxes.map((box, index) => (
            <div
              key={index}
              className="p-2 bg-white rounded border border-gray-200 text-sm"
            >
              <p className="text-gray-700">{box.text}</p>
              <p className="text-xs text-gray-500">
                신뢰도: {(box.confidence * 100).toFixed(0)}%
              </p>
            </div>
          ))}

          {/* {result.text_boxes.length > 5 && (
            <p className="text-xs text-gray-500 text-center">
              +{result.text_boxes.length - 5}개 더보기
            </p>
          )} */}
        </div>
      </div>
    </div>
  );
};
