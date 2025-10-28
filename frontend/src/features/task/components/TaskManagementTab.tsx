
import React, { useEffect, useState } from 'react';
import { useCancelPipeline, usePipelineStatus, useExtractPdf, } from '../hooks';
import { formatDate } from '@/shared/utils';

interface TaskManagementTabProps {
}

export const TaskManagementTab: React.FC<TaskManagementTabProps> = ({
}) => {
  const [pipelineId, setPipelineId] = useState<string>('');
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
    if (!pipelineId) {
      alert('먼저 파이프라인을 시작해주세요.');
      return;
    }

    cancelPipelineMutation.mutate(pipelineId, {
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
          <div className="bg-white p-4 rounded border">
            <h4 className="font-medium text-gray-800 mb-2">1. PDF 업로드</h4>
            <p className="text-sm text-gray-600 mb-3">PDF 파일을 업로드하여 해당 PDF를 기반으로 AI 파이프라인을 진행한다.</p>

            <div className="mb-3 space-y-3">
              <div className="flex items-center space-x-3">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {selectedFile && (
                <div className="text-sm text-gray-600">
                  선택된 파일: {selectedFile.name}
                </div>
              )}

              <div className="flex items-center space-x-3">
                <button
                  onClick={handleUpload}
                  disabled={!selectedFile}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  업로드
                </button>
              </div>
            </div>

            <div className="bg-gray-100 p-3 rounded text-xs font-mono overflow-x-auto">
              <div className="text-gray-600">curl 명령어 (예시):</div>
              <div className="mt-1">
                curl -X POST -F "pdf_file=@/path/to/your/file.pdf" "http://localhost:8000/api/v1/extract/pdf"
              </div>
            </div>
          </div>

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
                curl "http://localhost:8000/api/v1/pipeline/status/&#123;chain_id&#125;"
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
                disabled={!pipelineId || cancelPipelineMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {cancelPipelineMutation.isPending ? '취소 중...' : '파이프라인 취소'}
              </button>
            </div>

            <div className="bg-gray-100 p-3 rounded text-xs font-mono overflow-x-auto">
              <div className="text-gray-600">curl 명령어:</div>
              <div className="mt-1">
                curl -X DELETE "http://localhost:8000/api/v1/pipelines/ai-pipeline/&#123;pipeline_id&#125;/cancel"
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
    </div>
  );
};
