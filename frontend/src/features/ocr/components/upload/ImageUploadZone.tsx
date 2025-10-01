import React, { useState, useRef } from 'react';

interface ImageUploadZoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export const ImageUploadZone: React.FC<ImageUploadZoneProps> = ({
  onFileSelect,
  disabled = false,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (disabled) return;

    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      onFileSelect(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  };

  return (
    <div
      className={`
        relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-colors
        ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-blue-400'}
      `}
      onDrop={handleDrop}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onClick={() => !disabled && fileInputRef.current?.click()}
    >
      <div className="space-y-2">
        <div className="text-4xl">📁</div>
        <p className="font-semibold text-gray-700">
          이미지를 드래그하거나 클릭하세요
        </p>
        <p className="text-sm text-gray-500">JPG, PNG 등 이미지 파일</p>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        disabled={disabled}
        className="hidden"
      />
    </div>
  );
};
