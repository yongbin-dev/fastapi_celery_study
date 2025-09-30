import React, { useState, type ChangeEvent, useCallback, useRef } from 'react';

import { useExtractText } from '../hooks/useOcr';

import Modal from '@/shared/components/ui/Modal';
import OcrImage from '../components/OcrImage';
import type { OcrResponse } from '../types/ocr';

const UploadIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    {...props}
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M12 16.5V9.75m0 0l-3.75 3.75M12 9.75l3.75 3.75M3 17.25V21h18v-3.75M3.75 14.25c-.621 0-1.125-.504-1.125-1.125V11.25c0-.621.504-1.125 1.125-1.125h16.5c.621 0 1.125.504 1.125 1.125v1.875c0 .621-.504 1.125-1.125-1.125H3.75z"
    />
  </svg>
);

const OcrPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const mutation = useExtractText();

  const handleFileSelect = useCallback((file: File) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
    mutation.reset();
  }, [mutation]);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      mutation.mutate({ image_file: selectedFile });
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreview(null);
    mutation.reset();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      event.stopPropagation();
      setIsDragging(false);
      const file = event.dataTransfer.files?.[0];
      if (file && file.type.startsWith('image/')) {
        handleFileSelect(file);
      }
    },
    [handleFileSelect]
  );

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
  };

  const renderResultContent = (data: OcrResponse) => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-2">전체 텍스트</h3>
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 max-h-60 overflow-y-auto">
          <p className="text-gray-600 whitespace-pre-wrap">{data.full_text}</p>
        </div>
      </div>
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-2">
          인식된 텍스트 상자 ({data.total_boxes}개)
        </h3>
        <div className="max-h-80 overflow-y-auto space-y-2 pr-2">
          {data.text_boxes.map((box, index) => (
            <div key={index} className="p-3 bg-white rounded-md border border-gray-200">
              <p className="text-sm text-gray-700">{box.text}</p>
              <p className="text-xs text-gray-500 mt-1">
                신뢰도: {(box.confidence * 100).toFixed(2)}%
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full bg-gray-50 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-6xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden grid grid-cols-1 md:grid-cols-2">
        {/* Left Column: Upload & Preview */}
        <div className="p-8 border-r border-gray-200">
          <div className="flex flex-col h-full">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-800">OCR 이미지 텍스트 추출</h1>
              <p className="text-gray-500 mt-1">이미지에서 텍스트를 자동으로 인식하고 추출합니다.</p>
            </div>

            {!preview ? (
              <div
                className={`flex-grow flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-lg transition-colors duration-200 ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50'
                  }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                <UploadIcon className="w-12 h-12 text-gray-400 mb-4" />
                <p className="text-gray-600 font-semibold">이미지 파일을 여기로 드래그하세요.</p>
                <p className="text-sm text-gray-500 mt-1">또는 클릭하여 파일 선택</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </div>
            ) : (
              <div className="flex-grow flex flex-col">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">이미지 미리보기</h2>
                <div className="relative flex-grow rounded-lg overflow-hidden border border-gray-200">
                  {
                    mutation.isSuccess ? (
                      <OcrImage imageUrl={preview} textBoxes={mutation.data.text_boxes} />
                    ) : (
                      <img src={preview} alt="Preview" className="w-full h-full object-contain" />
                    )

                  }

                </div>
              </div>
            )}

            <div className="mt-6 flex space-x-3">
              <button
                onClick={handleUpload}
                disabled={!selectedFile || mutation.isPending}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {mutation.isPending ? '텍스트 추출 중...' : '텍스트 추출'}
              </button>
              {preview && (
                <button
                  onClick={handleClear}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  지우기
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Results */}
        <div className="p-8 bg-gray-50/50">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">추출 결과</h2>
          <div className="h-[500px] overflow-y-auto pr-2">
            {mutation.isIdle && !preview && (
              <div className="flex items-center justify-center h-full text-gray-500">
                <p>이미지를 업로드하면 결과가 여기에 표시됩니다.</p>
              </div>
            )}
            {mutation.isIdle && preview && (
              <div className="flex items-center justify-center h-full text-gray-500">
                <p>'텍스트 추출' 버튼을 클릭하여 분석을 시작하세요.</p>
              </div>
            )}
            {mutation.isPending && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                  <p className="mt-3 text-gray-600">텍스트를 추출하고 있습니다...</p>
                </div>
              </div>
            )}
            {mutation.isError && (
              <div className="flex items-center justify-center h-full text-red-500 bg-red-50 p-4 rounded-lg">
                <p>오류: {mutation.error.message}</p>
              </div>
            )}
            {mutation.isSuccess && (
              <div>
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-lg mb-6 transition-colors duration-200"
                >
                  이미지에서 텍스트 위치 보기
                </button>
                {renderResultContent(mutation.data)}
              </div>
            )}
          </div>
        </div>
      </div>

      {preview && mutation.isSuccess && (
        <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} >
          <OcrImage imageUrl={preview} textBoxes={mutation.data.text_boxes} />
        </Modal>
      )}
    </div>
  );
};

export default OcrPage;