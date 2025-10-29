
import React, { useEffect, useState } from 'react';
import { useCancelPipeline, usePipelineStatus, useExtractPdf, } from '../hooks';
import { formatDate } from '@/shared/utils';

interface TaskManagementTabProps {
}

export const TaskManagementTab: React.FC<TaskManagementTabProps> = ({
}) => {
  const [pipelineId, setPipelineId] = useState<string>('');
  const [cancelPipelineId, setCancelPipelineId] = useState<string>('');
  const [isAutoRefresh, setIsAutoRefresh] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // React Query 훅들
  const extractPdfMutation = useExtractPdf();
  const cancelPipelineMutation = useCancelPipeline();

  // 파이프라인 상태 조회 (자동 새로고침이 활성화된 경우에만 폴링)
  const {
    data: pipelineStatus,
    refetch: refetchStatus
  } = usePipelineStatus(
    pipelineId,
    isAutoRefresh && !!pipelineId, // 자동 새로고침이 활성화되고 pipelineId가 있을 때만 활성화
    isAutoRefresh ? 2000 : undefined // 자동 새로고침이 활성화되면 2초마다
  );


  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      extractPdfMutation.mutate(selectedFile, {
        onSuccess: (data) => {
          alert('PDF 업로드 성공: ' + JSON.stringify(data, null, 2));
        },
        onError: (error) => {
          alert('업로드 실패: ' + error.message);
        }
      });
    }
  };

  const handleCheckStatus = (silent = false) => {
    if (!pipelineId) {
      if (!silent) alert('먼저 파이프라인을 시작해주세요.');
      return;
    }
    refetchStatus();
  };

  const handleCancelPipeline = () => {
    if (!cancelPipelineId) {
      alert('먼저 파이프라인을 시작해주세요.');
      return;
    }

    cancelPipelineMutation.mutate(cancelPipelineId, {
      onSuccess: () => {
        alert('파이프라인이 취소되었습니다.');
        setPipelineId('');
        setIsAutoRefresh(false);
      },
      onError: (error) => {
        alert('파이프라인 취소 실패: ' + error);
      }
    });
  };

  // 파이프라인 완료/실패 시 자동 새로고침 중단
  useEffect(() => {
    if (pipelineStatus?.status === 'SUCCESS' || pipelineStatus?.status === 'FAILURE') {
      setIsAutoRefresh(false);
    }
  }, [pipelineStatus]);

  const renderJson = (jsonString: string | null | undefined) => {
    if (!jsonString) return <pre>N/A</pre>;
    try {
      const obj = JSON.parse(jsonString);
      return <pre>{JSON.stringify(obj, null, 2)}</pre>;
    } catch (e) {
      return <pre>{jsonString}</pre>;
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="text-center">
        <h2 className="text-2xl font-semibold mb-2">태스크 관리</h2>
        <p className="text-gray-600">AI 파이프라인 API 테스트 및 태스크 관리</p>
      </div>

      {/* AI 파이프라인 API 테스트 */}
      <div className="p-6 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-4">AI 파이프라인 API 테스트</h3>

        {pipelineId && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
            <p className="text-sm text-blue-700">
              <strong>현재 파이프라인 ID:</strong> {pipelineId}
            </p>
          </div>
        )}

        {/* 파이프라인 상태 표시 */}
        {
          pipelineStatus && (
            <div className="mb-6 p-4 bg-white rounded-lg border">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-semibold text-gray-800">파이프라인 진행 상황</h4>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${pipelineStatus.status === 'SUCCESS' ? 'bg-green-100 text-green-700' :
                  pipelineStatus.status === 'FAILURE' ? 'bg-red-100 text-red-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                  {pipelineStatus.status}
                </span>
              </div>

              {/* 전체 진행률 */}
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">전체 태스크</span>
                  <span className="text-sm text-gray-500">{pipelineStatus.completed_tasks} / {pipelineStatus.total_tasks}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(pipelineStatus.completed_tasks / pipelineStatus.total_tasks) * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* 체인 정보 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 p-3 bg-blue-50 rounded">
                <p className="text-sm text-blue-700"><strong>Chain ID:</strong> {pipelineStatus.chain_id}</p>
                <p className="text-sm text-blue-700"><strong>Chain Name:</strong> {pipelineStatus.chain_name}</p>
                <p className="text-sm text-blue-700"><strong>Created At:</strong> {formatDate(pipelineStatus.created_at)}</p>
                <p className="text-sm text-blue-700"><strong>Started At:</strong> {formatDate(pipelineStatus.started_at)}</p>
                <p className="text-sm text-blue-700"><strong>Finished At:</strong> {formatDate(pipelineStatus.finished_at)}</p>
                <p className="text-sm text-blue-700"><strong>Initiated By:</strong> {pipelineStatus.initiated_by}</p>
              </div>

              <div className="mb-4 p-3 bg-gray-100 rounded">
                <h5 className="font-medium text-gray-800 mb-2">Input Data</h5>
                <div className="text-xs text-gray-600 overflow-x-auto">
                  {renderJson(JSON.stringify(pipelineStatus.input_data))}
                </div>
              </div>


              {/* 태스크 목록 */}
              <div>
                <h5 className="font-medium text-gray-800 mb-4">Tasks</h5>
                <div className="flow-root">
                  <ul className="-mb-8">
                    {pipelineStatus.task_logs.map((task, taskIdx) => (
                      <li key={task.id}>
                        <div className="relative pb-8">
                          {taskIdx !== pipelineStatus.task_logs.length - 1 ? (
                            <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                          ) : null}
                          <div className="relative flex space-x-3">
                            <div>
                              <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${task.status === 'SUCCESS' ? 'bg-green-500' :
                                task.status === 'FAILURE' ? 'bg-red-500' :
                                  'bg-blue-500' // In-progress or pending
                                }`}>
                                {task.status === 'SUCCESS' ? (
                                  <svg className="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                  </svg>
                                ) : task.status === 'FAILURE' ? (
                                  <svg className="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                  </svg>
                                ) : (
                                  <svg className="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.414-1.414L11 9.586V6z" clipRule="evenodd" />
                                  </svg>
                                )}
                              </span>
                            </div>
                            <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                              <div>
                                <p className="text-sm text-gray-500">
                                  {task.task_name}{' '}
                                  <span className={`font-medium ${task.status === 'SUCCESS' ? 'text-green-600' :
                                    task.status === 'FAILURE' ? 'text-red-600' :
                                      'text-blue-600'
                                    }`}>({task.status})</span>
                                </p>
                                <p className="text-xs text-gray-400 mt-1">Task ID: {task.task_id}</p>
                              </div>
                              <div className="text-right text-xs whitespace-nowrap text-gray-500">
                                <p>Start: {formatDate(task.started_at)}</p>
                                <p>Finish: {formatDate(task.finished_at)}</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

            </div>
          )
        }

        <div className="space-y-6">


          {/* 1. PDF 업로드 */}
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
                <label className="block">
                  <div className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all ${selectedFile
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                    }`}>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handleFileChange}
                      className="hidden"
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
                  onClick={handleUpload}
                  disabled={!selectedFile || extractPdfMutation.isPending}
                  className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md flex items-center justify-center space-x-2"
                >
                  {extractPdfMutation.isPending ? (
                    <>
                      <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>업로드 중...</span>
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

              {/* curl 명령어 */}
              <details className="group">
                <summary className="flex items-center justify-between cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 py-2">
                  <span>API 호출 예시 보기</span>
                  <svg className="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </summary>
                <div className="mt-2 bg-gray-900 p-4 rounded-lg overflow-x-auto">
                  <code className="text-xs text-green-400 font-mono">
                    curl -X POST -F "pdf_file=@/path/to/your/file.pdf" \<br />
                    &nbsp;&nbsp;"http://localhost:8000/api/v1/extract/pdf"
                  </code>
                </div>
              </details>
            </div>
          </div>

          {/* 2. 진행 상태 확인 */}
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <div className="flex items-center mb-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 text-green-600 font-semibold mr-3">
                2
              </div>
              <h4 className="font-semibold text-gray-800">진행 상태 확인</h4>
            </div>
            <p className="text-sm text-gray-600 mb-4 ml-11">실행 중인 파이프라인의 상태를 확인합니다.</p>

            <div className="ml-11 space-y-4">
              {/* 파이프라인 ID 입력 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  파이프라인 ID
                </label>
                <input
                  type="text"
                  value={pipelineId}
                  onChange={(e) => setPipelineId(e.target.value)}
                  placeholder="파이프라인 ID를 입력하세요"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                />
              </div>

              {/* 버튼 그룹 */}
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => handleCheckStatus(false)}
                  disabled={!pipelineId}
                  className="flex-1 min-w-[140px] px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white font-medium rounded-lg hover:from-green-700 hover:to-green-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md flex items-center justify-center space-x-2"
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>상태 확인</span>
                </button>

                <button
                  onClick={() => setIsAutoRefresh(!isAutoRefresh)}
                  disabled={!pipelineId}
                  className={`flex-1 min-w-[180px] px-6 py-3 font-medium rounded-lg transition-all shadow-sm hover:shadow-md disabled:cursor-not-allowed disabled:from-gray-300 disabled:to-gray-400 flex items-center justify-center space-x-2 ${isAutoRefresh
                    ? 'bg-gradient-to-r from-orange-600 to-orange-700 text-white hover:from-orange-700 hover:to-orange-800'
                    : 'bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800'
                    }`}
                >
                  {isAutoRefresh ? (
                    <>
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>자동 새로고침 중지</span>
                    </>
                  ) : (
                    <>
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      <span>자동 새로고침 시작</span>
                    </>
                  )}
                </button>
              </div>

              {/* 자동 새로고침 상태 표시 */}
              {isAutoRefresh && (
                <div className="flex items-center space-x-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                  <span className="text-sm font-medium text-blue-700">2초마다 자동 업데이트 중</span>
                </div>
              )}

              {/* curl 명령어 */}
              <details className="group">
                <summary className="flex items-center justify-between cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 py-2">
                  <span>API 호출 예시 보기</span>
                  <svg className="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </summary>
                <div className="mt-2 bg-gray-900 p-4 rounded-lg overflow-x-auto">
                  <code className="text-xs text-green-400 font-mono">
                    curl "http://localhost:8000/api/v1/pipeline/status/&#123;chain_id&#125;"
                  </code>
                </div>
              </details>
            </div>
          </div>

          {/* 3. 파이프라인 취소 */}
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <div className="flex items-center mb-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-red-100 text-red-600 font-semibold mr-3">
                3
              </div>
              <h4 className="font-semibold text-gray-800">파이프라인 취소</h4>
            </div>
            <p className="text-sm text-gray-600 mb-4 ml-11">실행 중인 파이프라인을 취소합니다.</p>

            <div className="ml-11 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  취소 파이프라인 ID
                </label>
                <input
                  type="text"
                  value={cancelPipelineId}
                  onChange={(e) => setCancelPipelineId(e.target.value)}
                  placeholder="취소 할 파이프라인 ID를 입력하세요"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all"
                />
              </div>

              {/* 경고 메시지 */}
              <div className="flex items-start space-x-3 p-4 bg-red-50 border border-red-200 rounded-lg">
                <svg className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-red-800">주의사항</p>
                  <p className="text-xs text-red-700 mt-1">
                    취소된 파이프라인은 복구할 수 없습니다. 진행 중인 작업이 즉시 중단됩니다.
                  </p>
                </div>
              </div>

              {/* 취소 버튼 */}
              <button
                onClick={handleCancelPipeline}
                disabled={!cancelPipelineId || cancelPipelineMutation.isPending}
                className="w-full px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white font-medium rounded-lg hover:from-red-700 hover:to-red-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md flex items-center justify-center space-x-2"
              >
                {cancelPipelineMutation.isPending ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>취소 중...</span>
                  </>
                ) : (
                  <>
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span>파이프라인 취소</span>
                  </>
                )}
              </button>

              {/* curl 명령어 */}
              <details className="group">
                <summary className="flex items-center justify-between cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 py-2">
                  <span>API 호출 예시 보기</span>
                  <svg className="w-5 h-5 text-gray-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </summary>
                <div className="mt-2 bg-gray-900 p-4 rounded-lg overflow-x-auto">
                  <code className="text-xs text-green-400 font-mono">
                    curl -X DELETE \<br />
                    &nbsp;&nbsp;"http://localhost:8000/api/v1/pipelines/ai-pipeline/&#123;pipeline_id&#125;/cancel"
                  </code>
                </div>
              </details>
            </div>
          </div>

          {/* 사용 순서 안내 */}
          <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border-l-4 border-yellow-400 p-6 rounded-lg shadow-sm">
            <div className="flex items-start space-x-3">
              <svg className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <div className="flex-1">
                <h4 className="font-semibold text-yellow-900 mb-3 text-lg">사용 방법</h4>
                <ol className="space-y-3">
                  <li className="flex items-start space-x-3">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-yellow-200 text-yellow-800 text-xs font-bold flex-shrink-0 mt-0.5">1</span>
                    <p className="text-sm text-yellow-800">PDF 파일을 선택하고 <strong>"PDF 업로드 및 파이프라인 시작"</strong> 버튼을 클릭하세요.</p>
                  </li>
                  <li className="flex items-start space-x-3">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-yellow-200 text-yellow-800 text-xs font-bold flex-shrink-0 mt-0.5">2</span>
                    <p className="text-sm text-yellow-800">응답으로 받은 파이프라인 ID를 복사하여 <strong>"진행 상태 확인"</strong> 섹션에 입력하세요.</p>
                  </li>
                  <li className="flex items-start space-x-3">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-yellow-200 text-yellow-800 text-xs font-bold flex-shrink-0 mt-0.5">3</span>
                    <p className="text-sm text-yellow-800"><strong>"상태 확인"</strong> 또는 <strong>"자동 새로고침 시작"</strong> 버튼으로 진행 상황을 모니터링할 수 있습니다.</p>
                  </li>
                  <li className="flex items-start space-x-3">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-yellow-200 text-yellow-800 text-xs font-bold flex-shrink-0 mt-0.5">4</span>
                    <p className="text-sm text-yellow-800">필요시 <strong>"파이프라인 취소"</strong> 버튼으로 실행을 중단할 수 있습니다.</p>
                  </li>
                </ol>
                <div className="mt-4 pt-4 border-t border-yellow-200">
                  <p className="text-xs text-yellow-700 flex items-center space-x-2">
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>각 섹션의 "API 호출 예시 보기"를 펼쳐서 curl 명령어로도 직접 API를 호출할 수 있습니다.</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
