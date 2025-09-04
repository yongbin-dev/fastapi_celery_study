import React, { useRef, useState } from 'react';
import { useImageTask } from '../hooks';
import type { ModelTestRequest } from '../types';

export const TaskModelsTab: React.FC = () => {

  const { mutateAsync } = useImageTask();

  const [images, setImages] = useState<{
    image1: File | null;
    image2: File | null;
  }>({
    image1: null,
    image2: null,
  });


  const [previews, setPreviews] = useState<{
    image1: string | null;
    image2: string | null;
  }>({
    image1: null,
    image2: null,
  });

  const fileInput1Ref = useRef<HTMLInputElement>(null);
  const fileInput2Ref = useRef<HTMLInputElement>(null);

  const handleImageUpload = (imageKey: 'image1' | 'image2', file: File | null) => {
    setImages(prev => ({
      ...prev,
      [imageKey]: file,
    }));

    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviews(prev => ({
          ...prev,
          [imageKey]: e.target?.result as string,
        }));
      };
      reader.readAsDataURL(file);
    } else {
      setPreviews(prev => ({
        ...prev,
        [imageKey]: null,
      }));
    }
  };

  const handleFileInputChange = (imageKey: 'image1' | 'image2') => (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    handleImageUpload(imageKey, file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (imageKey: 'image1' | 'image2') => (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      handleImageUpload(imageKey, file);
    }
  };

  const removeImage = (imageKey: 'image1' | 'image2') => {
    handleImageUpload(imageKey, null);
    if (imageKey === 'image1' && fileInput1Ref.current) {
      fileInput1Ref.current.value = '';
    }
    if (imageKey === 'image2' && fileInput2Ref.current) {
      fileInput2Ref.current.value = '';
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!images.image1 || !images.image2) {
      alert('두 개의 이미지를 모두 업로드해주세요.');
      return;
    }

    const data: ModelTestRequest = {
      image1: images.image1,
      image2: images.image2
    }

    mutateAsync(data).then((resp) => {
      console.log(resp)
    })
    // 여기에 실제 업로드 로직 추가
    console.log('업로드할 이미지들:', images);
    alert('이미지 업로드가 완료되었습니다!');
  };


  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center">
        <h2 className="text-2xl font-semibold mb-2">모델 테스트</h2>
        <p className="text-gray-600">두 개의 이미지를 업로드하여 모델을 테스트해보세요.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* 첫 번째 이미지 업로드 */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">첫 번째 이미지</h3>

            <div
              className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors cursor-pointer"
              onDragOver={handleDragOver}
              onDrop={handleDrop('image1')}
              onClick={() => fileInput1Ref.current?.click()}
            >
              {previews.image1 ? (
                <div className="relative">
                  <img
                    src={previews.image1}
                    alt="첫 번째 이미지 미리보기"
                    className="max-w-full max-h-64 mx-auto rounded-lg shadow-md"
                  />
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeImage('image1');
                    }}
                    className="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-600 transition-colors"
                  >
                    ×
                  </button>
                </div>
              ) : (
                <div className="py-8">
                  <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <div className="mt-4">
                    <p className="text-sm text-gray-600">
                      <span className="font-medium text-blue-600 hover:text-blue-500">클릭하여 파일 선택</span>
                      <span className="text-gray-500"> 또는 드래그 앤 드롭</span>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">PNG, JPG, GIF 최대 10MB</p>
                  </div>
                </div>
              )}
            </div>

            <input
              ref={fileInput1Ref}
              type="file"
              accept="image/*"
              onChange={handleFileInputChange('image1')}
              className="hidden"
            />
          </div>

          {/* 두 번째 이미지 업로드 */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">두 번째 이미지</h3>

            <div
              className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors cursor-pointer"
              onDragOver={handleDragOver}
              onDrop={handleDrop('image2')}
              onClick={() => fileInput2Ref.current?.click()}
            >
              {previews.image2 ? (
                <div className="relative">
                  <img
                    src={previews.image2}
                    alt="두 번째 이미지 미리보기"
                    className="max-w-full max-h-64 mx-auto rounded-lg shadow-md"
                  />
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeImage('image2');
                    }}
                    className="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-600 transition-colors"
                  >
                    ×
                  </button>
                </div>
              ) : (
                <div className="py-8">
                  <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <div className="mt-4">
                    <p className="text-sm text-gray-600">
                      <span className="font-medium text-blue-600 hover:text-blue-500">클릭하여 파일 선택</span>
                      <span className="text-gray-500"> 또는 드래그 앤 드롭</span>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">PNG, JPG, GIF 최대 10MB</p>
                  </div>
                </div>
              )}
            </div>

            <input
              ref={fileInput2Ref}
              type="file"
              accept="image/*"
              onChange={handleFileInputChange('image2')}
              className="hidden"
            />
          </div>
        </div>

        {/* 업로드 상태 및 제출 버튼 */}
        <div className="text-center space-y-4">
          <div className="flex justify-center space-x-4 text-sm">
            <div className={`flex items-center space-x-2 ${images.image1 ? 'text-green-600' : 'text-gray-400'}`}>
              <div className={`w-3 h-3 rounded-full ${images.image1 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span>첫 번째 이미지</span>
            </div>
            <div className={`flex items-center space-x-2 ${images.image2 ? 'text-green-600' : 'text-gray-400'}`}>
              <div className={`w-3 h-3 rounded-full ${images.image2 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span>두 번째 이미지</span>
            </div>
          </div>

          <div className="flex justify-center">
            <button
              type="submit"
              disabled={!images.image1 || !images.image2}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              모델 테스트 시작
            </button>
          </div>
        </div>
      </form>

    </div>
  );
};