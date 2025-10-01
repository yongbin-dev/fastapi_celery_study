import React from 'react';
import { ImageUploadZone } from '../upload/ImageUploadZone';
import { ImagePreview } from '../upload/ImagePreview';
import { OcrResultDisplay } from '../results/OcrResultDisplay';
import type { ImageSlot } from '../../types/comparison';

interface ImagePanelProps {
  slot: ImageSlot;
  onFileSelect: (file: File) => void;
  onExtract: () => void;
  onClear: () => void;
}

export const ImagePanel: React.FC<ImagePanelProps> = ({
  slot,
  onFileSelect,
  onExtract,
  onClear,
}) => {
  return (
    <div className="p-6 space-y-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">이미지 {slot.id}</h3>
        {slot.file && (
          <button
            onClick={onClear}
            className="text-sm text-gray-500 hover:text-red-600 transition-colors"
          >
            초기화
          </button>
        )}
      </div>

      {/* 업로드 영역 or 프리뷰 */}
      {!slot.preview ? (
        <ImageUploadZone
          onFileSelect={onFileSelect}
          disabled={slot.status === 'uploading'}
        />
      ) : (
        <ImagePreview
          imageUrl={slot.preview}
          fileName={slot.file?.name}
          fileSize={slot.file?.size}
        />
      )}

      {/* OCR 실행 버튼 */}
      {slot.preview && !slot.ocrResult && (
        <button
          onClick={onExtract}
          disabled={slot.status === 'extracting'}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {slot.status === 'extracting' ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              텍스트 추출 중...
            </span>
          ) : (
            '텍스트 추출'
          )}
        </button>
      )}

      {/* 에러 표시 */}
      {slot.status === 'error' && slot.error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{slot.error}</p>
        </div>
      )}

      {/* OCR 결과 */}
      {slot.ocrResult && <OcrResultDisplay result={slot.ocrResult} />}
    </div>
  );
};
