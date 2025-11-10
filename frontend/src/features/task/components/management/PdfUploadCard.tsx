import type { UseMutationResult } from '@tanstack/react-query';
import React, { useState } from 'react';

interface PdfUploadCardProps {
  selectedFile: File | null;
  onFileSelect: (file: File | null) => void;
  onUpload: () => void;
  extractPdfMutation: UseMutationResult<any, Error, File, unknown>;
  isLoading?: boolean;
}

export const PdfUploadCard: React.FC<PdfUploadCardProps> = ({
  selectedFile,
  onFileSelect,
  onUpload,
  extractPdfMutation,
  isLoading = false,
}) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    onFileSelect(file);
  };

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      // PDF 파일인지 확인
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        onFileSelect(file);
      } else {
        alert('PDF 파일만 업로드 가능합니다.');
      }
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex items-center mb-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold mr-3">
          1
        </div>
        <h4 className="font-semibold text-gray-800">PDF 업로드</h4>
      </div>
      <p className="text-sm text-gray-600 mb-4 ml-11">PDF 파일을 업로드하여 AI 파이프라인을 시작합니다.</p>

      <div className="ml-11 space-y-4">
        {/* 파일 업로드 영역 */}
        <div className="relative">
          <label className={`block ${isLoading ? 'cursor-not-allowed' : ''}`}>
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-all ${
                isLoading
                  ? 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
                  : isDragging
                  ? 'border-blue-500 bg-blue-100 cursor-pointer'
                  : selectedFile
                  ? 'border-blue-400 bg-blue-50 cursor-pointer'
                  : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50 cursor-pointer'
              }`}
              onDragEnter={isLoading ? undefined : handleDragEnter}
              onDragLeave={isLoading ? undefined : handleDragLeave}
              onDragOver={isLoading ? undefined : handleDragOver}
              onDrop={isLoading ? undefined : handleDrop}
            >
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
                disabled={isLoading}
              />

              {/* 아이콘 */}
              <div className="mb-3">
                <svg
                  className={`mx-auto h-12 w-12 ${selectedFile ? 'text-blue-500' : 'text-gray-400'}`}
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                  aria-hidden="true"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>

              {/* 텍스트 */}
              {selectedFile ? (
                <div>
                  <p className="text-sm font-medium text-blue-700 mb-1">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                  <p className="text-xs text-blue-600 mt-2">
                    다른 파일을 선택하려면 클릭하세요
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">
                    PDF 파일을 드래그하거나 클릭하여 선택
                  </p>
                  <p className="text-xs text-gray-500">
                    PDF 형식만 지원됩니다
                  </p>
                </div>
              )}
            </div>
          </label>
        </div>

        {/* 업로드 버튼 */}
        <div>
          <button
            onClick={onUpload}
            disabled={!selectedFile || isLoading}
            className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md flex items-center justify-center space-x-2"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>처리 중...</span>
              </>
            ) : (
              <>
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span>PDF 업로드 및 파이프라인 시작</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
