import React, { useState, useRef, useEffect } from 'react';
import { useImageTask } from '../hooks';
import type { ModelTestRequest } from '../types';

const TEST_URL = "localhost:8000";

export const TaskModelsTab: React.FC = () => {

  const { mutateAsync } = useImageTask();

  const [images, setImages] = useState<{
    image1: File | null;
    image2: File | null;
  }>({
    image1: null,
    image2: null,
  });

  const [showApiGuide, setShowApiGuide] = useState(false);
  const [pipelineId, setPipelineId] = useState<string>('');
  const [pipelineStatus, setPipelineStatus] = useState<any>(null);
  const [isAutoRefresh, setIsAutoRefresh] = useState(false);

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

  const handleStartPipeline = async () => {
    try {
      const response = await fetch(`http://${TEST_URL}/api/v1/tasks/ai-pipeline`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: '분석할 텍스트',
          options: { model: 'bert' }
        }),
      });

      const result = await response.json();
      const pipelineIdValue = result.data?.pipeline_id || result.pipeline_id || result.id || '';
      setPipelineId(pipelineIdValue);
      alert(`파이프라인이 시작되었습니다! ID: ${pipelineIdValue}`);
    } catch (error) {
      alert('파이프라인 시작 실패: ' + error);
    }
  };

  const handleCheckStatus = async (silent = false) => {
    if (!pipelineId) {
      if (!silent) alert('먼저 파이프라인을 시작해주세요.');
      return;
    }

    try {
      const response = await fetch(`http://${TEST_URL}/api/v1/tasks/ai-pipeline/${pipelineId}/status`);
      const result = await response.json();
      setPipelineStatus(result.data);

      // 파이프라인이 완료되거나 실패하면 자동 새로고침 중단
      if (result.data?.status === 'COMPLETED' || result.data?.status === 'FAILED') {
        setIsAutoRefresh(false);
      }
    } catch (error) {
      if (!silent) alert('상태 확인 실패: ' + error);
    }
  };

  // 자동 새로고침 효과
  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (isAutoRefresh && pipelineId) {
      interval = setInterval(() => {
        handleCheckStatus(true); // silent 모드로 호출
      }, 2000); // 2초마다 업데이트
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isAutoRefresh, pipelineId]);

  const handleCancelPipeline = async () => {
    if (!pipelineId) {
      alert('먼저 파이프라인을 시작해주세요.');
      return;
    }

    try {
      await fetch(`http://${TEST_URL}/api/v1/tasks/ai-pipeline/${pipelineId}/cancel`, {
        method: 'DELETE',
      });
      alert('파이프라인이 취소되었습니다.');
      setPipelineId('');
      setPipelineStatus(null);
      setIsAutoRefresh(false);
    } catch (error) {
      alert('파이프라인 취소 실패: ' + error);
    }
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

          <div className="flex justify-center space-x-4">
            <button
              type="submit"
              disabled={!images.image1 || !images.image2}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              모델 테스트 시작
            </button>

            <button
              type="button"
              onClick={() => setShowApiGuide(!showApiGuide)}
              className="px-8 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors"
            >
              API 테스트 가이드
            </button>
          </div>
        </div>
      </form>

      {/* API 테스트 가이드 섹션 */}
      {showApiGuide && (
        <div className="mt-8 p-6 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">AI 파이프라인 API 테스트</h3>

          {pipelineId && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
              <p className="text-sm text-blue-700">
                <strong>현재 파이프라인 ID:</strong> {pipelineId}
              </p>
            </div>
          )}

          {/* 파이프라인 상태 표시 */}
          {pipelineStatus && (
            <div className="mb-6 p-4 bg-white rounded-lg border">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-semibold text-gray-800">파이프라인 진행 상황</h4>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${pipelineStatus.status === 'STARTED' ? 'bg-blue-100 text-blue-700' :
                  pipelineStatus.status === 'COMPLETED' ? 'bg-green-100 text-green-700' :
                    pipelineStatus.status === 'FAILED' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                  }`}>
                  {pipelineStatus.status}
                </span>
              </div>

              {/* 전체 진행률 */}
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">전체 진행률</span>
                  <span className="text-sm text-gray-500">{pipelineStatus.overall_progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${pipelineStatus.overall_progress}%` }}
                  ></div>
                </div>
              </div>

              {/* 현재 단계 */}
              <div className="mb-4 p-3 bg-blue-50 rounded">
                <p className="text-sm text-blue-700">
                  <strong>현재 단계:</strong> {pipelineStatus.current_stage_name} (단계 {pipelineStatus.current_stage})
                </p>
              </div>

              {/* 단계별 상태 */}
              <div className="space-y-3">
                <h5 className="font-medium text-gray-800">단계별 상태</h5>
                {pipelineStatus.stages?.map((stage: any) => (
                  <div key={stage.stage} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${stage.status === 'COMPLETED' ? 'bg-green-500' :
                        stage.status === 'RUNNING' ? 'bg-blue-500' :
                          stage.status === 'FAILED' ? 'bg-red-500' :
                            'bg-gray-300'
                        }`}></div>
                      <span className="text-sm font-medium">{stage.stage}. {stage.stage_name}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${stage.status === 'COMPLETED' ? 'bg-green-100 text-green-700' :
                        stage.status === 'RUNNING' ? 'bg-blue-100 text-blue-700' :
                          stage.status === 'FAILED' ? 'bg-red-100 text-red-700' :
                            'bg-gray-100 text-gray-700'
                        }`}>
                        {stage.status}
                      </span>
                      <span className="text-xs text-gray-500">{stage.progress}%</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* 결과 또는 에러 표시 */}
              {pipelineStatus.result && (
                <div className="mt-4 p-3 bg-green-50 rounded">
                  <h6 className="font-medium text-green-800 mb-2">결과</h6>
                  <pre className="text-xs text-green-700 overflow-auto">
                    {JSON.stringify(pipelineStatus.result, null, 2)}
                  </pre>
                </div>
              )}

              {pipelineStatus.error && (
                <div className="mt-4 p-3 bg-red-50 rounded">
                  <h6 className="font-medium text-red-800 mb-2">오류</h6>
                  <pre className="text-xs text-red-700 overflow-auto">
                    {JSON.stringify(pipelineStatus.error, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}

          <div className="space-y-6">
            {/* 1. 파이프라인 시작 */}
            <div className="bg-white p-4 rounded border">
              <h4 className="font-medium text-gray-800 mb-2">1. 파이프라인 시작</h4>
              <p className="text-sm text-gray-600 mb-3">텍스트 분석을 위한 AI 파이프라인을 시작합니다.</p>

              <div className="mb-3">
                <button
                  onClick={handleStartPipeline}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  파이프라인 시작
                </button>
              </div>

              <div className="bg-gray-100 p-3 rounded text-xs font-mono overflow-x-auto">
                <div className="text-gray-600">curl 명령어:</div>
                <div className="mt-1">
                  curl -X POST "http://localhost:8000/api/v1/tasks/ai-pipeline" \<br />
                  &nbsp;&nbsp;-H "Content-Type: application/json" \<br />
                  &nbsp;&nbsp;-d '&#123;"text": "분석할 텍스트", "options": &#123;"model": "bert"&#125;&#125;'
                </div>
              </div>
            </div>

            {/* 2. 진행 상태 확인 */}
            <div className="bg-white p-4 rounded border">
              <h4 className="font-medium text-gray-800 mb-2">2. 진행 상태 확인</h4>
              <p className="text-sm text-gray-600 mb-3">실행 중인 파이프라인의 상태를 확인합니다.</p>

              <div className="mb-3 space-y-3">
                <div className="flex items-center space-x-3">
                  <input
                    type="text"
                    value={pipelineId}
                    onChange={(e) => setPipelineId(e.target.value)}
                    placeholder="파이프라인 ID를 입력하세요"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => handleCheckStatus(false)}
                    disabled={!pipelineId}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    상태 확인
                  </button>

                  <button
                    onClick={() => setIsAutoRefresh(!isAutoRefresh)}
                    disabled={!pipelineId}
                    className={`px-4 py-2 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${isAutoRefresh
                      ? 'bg-orange-600 text-white hover:bg-orange-700'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                      }`}
                  >
                    {isAutoRefresh ? '자동 새로고침 중지' : '자동 새로고침 시작'}
                  </button>

                  {isAutoRefresh && (
                    <div className="flex items-center space-x-2 text-sm text-blue-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span>2초마다 자동 업데이트</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-gray-100 p-3 rounded text-xs font-mono overflow-x-auto">
                <div className="text-gray-600">curl 명령어:</div>
                <div className="mt-1">
                  curl "http://localhost:8000/api/v1/tasks/ai-pipeline/&#123;pipeline_id&#125;/status"
                </div>
              </div>
            </div>

            {/* 3. 파이프라인 취소 */}
            <div className="bg-white p-4 rounded border">
              <h4 className="font-medium text-gray-800 mb-2">3. 파이프라인 취소</h4>
              <p className="text-sm text-gray-600 mb-3">실행 중인 파이프라인을 취소합니다.</p>

              <div className="mb-3">
                <button
                  onClick={handleCancelPipeline}
                  disabled={!pipelineId}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  파이프라인 취소
                </button>
              </div>

              <div className="bg-gray-100 p-3 rounded text-xs font-mono overflow-x-auto">
                <div className="text-gray-600">curl 명령어:</div>
                <div className="mt-1">
                  curl -X DELETE "http://localhost:8000/api/v1/tasks/ai-pipeline/&#123;pipeline_id&#125;/cancel"
                </div>
              </div>
            </div>

            {/* 사용 순서 안내 */}
            <div className="bg-yellow-50 border border-yellow-200 p-4 rounded">
              <h4 className="font-medium text-yellow-800 mb-2">💡 사용 방법</h4>
              <ol className="text-sm text-yellow-700 space-y-1 list-decimal list-inside">
                <li>먼저 "파이프라인 시작" 버튼을 클릭하여 파이프라인을 시작하세요.</li>
                <li>파이프라인 ID가 생성되면 "상태 확인" 버튼으로 진행 상황을 모니터링할 수 있습니다.</li>
                <li>필요시 "파이프라인 취소" 버튼으로 실행을 중단할 수 있습니다.</li>
                <li>각 버튼 아래의 curl 명령어를 참고하여 직접 API를 호출할 수도 있습니다.</li>
              </ol>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};