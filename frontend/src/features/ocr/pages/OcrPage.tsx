import React, { useCallback, useRef, useState, type ChangeEvent } from 'react';

import { OcrResultDisplay } from '../components';
import { useExtractImage, useExtractText, useOcrResults } from '../hooks/useOcr';

import { Upload } from 'lucide-react';
import OcrImage from '../components/OcrImage';
import type { OcrResponse } from '../types/ocr';

const OcrPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedResult, setSelectedResult] = useState<OcrResponse | null>(
    null
  );
  const [selectedImagePath, setSelectedImagePath] = useState("https://ifhenrlmwkfsxibiwggf.supabase.co/storage/v1/object/public/yb_test_storage/uploads/2025-10-21/d260dd1b-2ba5-4bb7-b515-1824847b3dff_ocr_test.png")
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { data: ocrListData, isLoading: isListLoading, refetch } = useOcrResults();

  const mutation = useExtractText({
    onSuccess: (data: any) => {
      refetch();

      const publicIng = data.public_img;
      setSelectedImagePath(publicIng)

      // console.log(data)
      // setSelectedResult(data);
    },
  });


  const mutationImage = useExtractImage({
    onSuccess: (data: any) => {
      refetch();

      // console.log(data)
      // setSelectedResult(data);
    },
  });

  // useEffect(() => {

  // }, [selectedImagePath])


  const handleFileSelect = useCallback(
    (file: File) => {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
      mutation.reset();
    },
    [mutation]
  );

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

  const handleTest = () => {
    if (!selectedImagePath) return;
    mutationImage.mutate(selectedImagePath);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreview(null);
    setSelectedResult(null);
    mutation.reset();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSelectResult = (result: OcrResponse) => {
    setSelectedResult(result);
    setPreview(result.public_path);
    setSelectedFile(null);
    mutation.reset();
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

  return (
    <div className="h-full bg-gray-50 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-7xl mx-auto bg-white rounded-2xl shadow-lg overflow-hidden grid grid-cols-1 lg:grid-cols-3">
        {/* Left Column: OCR Results List */}
        <div className="p-6 border-r border-gray-200 bg-gray-50/50">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            OCR 결과 목록
          </h2>
          <div className="h-[600px] overflow-y-auto space-y-2">
            {isListLoading && (
              <div className="flex items-center justify-center py-8">
                <div className="w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            )}
            {ocrListData && ocrListData.length > 0
              ? ocrListData.map((result, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectResult(result)}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${selectedResult?.id === result.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/50'
                    }`}
                >
                  <div className="flex items-center space-x-3">
                    <img
                      src={result.public_path}
                      alt={`OCR Result ${result.id}`}
                      className="w-16 h-16 object-cover rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">
                        결과 #{result.id}
                      </p>
                      <p className="text-xs text-gray-500">
                        텍스트 박스: {result.text_boxes.length}개
                      </p>
                      <p className="text-xs text-gray-500 capitalize">
                        상태: {result.status}
                      </p>
                    </div>
                  </div>
                </button>
              ))
              : !isListLoading && (
                <div className="flex items-center justify-center h-full text-gray-500">
                  <p className="text-center">저장된 OCR 결과가 없습니다.</p>
                </div>
              )}
          </div>
        </div>

        {/* Middle Column: Upload & Preview */}
        <div className="p-8 border-r border-gray-200">
          <div className="flex flex-col h-full">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-800">
                OCR 이미지 텍스트 추출
              </h1>
              <p className="text-gray-500 mt-1">
                이미지에서 텍스트를 자동으로 인식하고 추출합니다.
              </p>
            </div>

            {!preview ? (
              <div
                className={`flex-grow flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-lg transition-colors duration-200 ${isDragging
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 bg-gray-50'
                  }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-12 h-12 text-gray-400 mb-4" />
                <p className="text-gray-600 font-semibold">
                  이미지 파일을 여기로 드래그하세요.
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  또는 클릭하여 파일 선택
                </p>
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
                <h2 className="text-xl font-semibold text-gray-800 mb-4">
                  이미지 미리보기
                </h2>
                <div className="relative flex-grow rounded-lg overflow-hidden border border-gray-200">
                  {selectedResult ? (
                    <OcrImage
                      imageUrl={preview}
                      textBoxes={selectedResult.text_boxes}
                    />
                  ) : (
                    <img
                      src={preview}
                      alt="Preview"
                      className="w-full h-full object-contain"
                    />
                  )}
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
              <button
                onClick={handleTest}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {mutation.isPending ? '텍스트 추출 중...' : '텍스트 추출'}
              </button>
              {preview && (
                <button
                  onClick={handleClear}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  지우기
                </button>
              )}
            </div>
          </div>
        </div>
        <div className="p-6 bg-gray-50/50 h-[700px] overflow-y-auto">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            추출 결과
          </h2>
          {mutation.isIdle && !selectedResult && (
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

          {selectedResult ? (
            <OcrResultDisplay result={selectedResult} />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <p>이미지를 선택하거나 업로드하여 결과를 확인하세요.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OcrPage;
