import React from 'react';

interface ImagePreviewProps {
  imageUrl: string;
  fileName?: string;
  fileSize?: number;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  imageUrl,
  fileName,
  fileSize,
}) => {
  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-3">
      {/* 이미지 프리뷰 */}
      <div className="relative rounded-lg overflow-hidden border border-gray-200 bg-gray-100">
        <img
          src={imageUrl}
          alt="Preview"
          className="w-full h-auto max-h-64 object-contain"
        />
      </div>

      {/* 파일 정보 */}
      {(fileName || fileSize) && (
        <div className="text-sm text-gray-600 space-y-1">
          {fileName && (
            <p className="truncate" title={fileName}>
              📄 {fileName}
            </p>
          )}
          {fileSize && <p>📊 {formatFileSize(fileSize)}</p>}
        </div>
      )}
    </div>
  );
};
