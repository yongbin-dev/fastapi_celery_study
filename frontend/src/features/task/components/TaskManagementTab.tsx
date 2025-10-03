
import React, { useEffect, useState } from 'react';
import { useCancelPipeline, usePipelineStatus, useStartPipeline } from '../hooks';
import { formatDate } from '@/shared/utils';

interface TaskManagementTabProps {
}

export const TaskManagementTab: React.FC<TaskManagementTabProps> = ({
}) => {
  const [pipelineId, setPipelineId] = useState<string>('');
  const [isAutoRefresh, setIsAutoRefresh] = useState(false);

  // React Query 훅들
  const startPipelineMutation = useStartPipeline();
  const cancelPipelineMutation = useCancelPipeline();

  // 파이프라인 상태 조회 (자동 새로고침 포함)
  const {
    data: pipelineStatus,
    refetch: refetchStatus
  } = usePipelineStatus(
    pipelineId,
    !!pipelineId, // pipelineId가 있을 때만 활성화
    isAutoRefresh ? 2000 : undefined // 자동 새로고침이 활성화되면 2초마다
  );

  const handleStartPipeline = () => {
    startPipelineMutation.mutate(
      {
        text: '분석할 텍스트',
        options: { model: 'bert' }
      },
      {
        onSuccess: (data) => {
          setPipelineId(data.pipeline_id);
          alert(`파이프라인이 시작되었습니다! ID: ${data.pipeline_id}`);
          setIsAutoRefresh(true);
        },
        onError: (error) => {
          alert('파이프라인 시작 실패: ' + error);
        }
      }
    );
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
        {pipelineStatus && (
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
            <div className="space-y-3">
              <h5 className="font-medium text-gray-800">Tasks</h5>
              {pipelineStatus.task_logs.map((task) => (
                <div key={task.id} className="p-3 bg-gray-50 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${task.status === 'SUCCESS' ? 'bg-green-500' :
                        task.status === 'PROGRESS' ? 'bg-blue-500' :
                          task.status === 'FAILURE' ? 'bg-red-500' :
                            'bg-gray-300'
                        }`}></div>
                      <span className="text-sm font-medium">
                        {task.task_name}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${task.status === 'SUCCESS' ? 'bg-green-100 text-green-700' :
                        task.status === 'PROGRESS' ? 'bg-blue-100 text-blue-700' :
                          task.status === 'FAILURE' ? 'bg-red-100 text-red-700' :
                            'bg-gray-100 text-gray-700'
                        }`}>
                        {task.status}
                      </span>
                    </div>
                  </div>
                  <div className="ml-6 space-y-1 text-xs text-gray-600">
                    <p><strong>Task ID:</strong> {task.task_id}</p>
                    <p><strong>Completed At:</strong> {formatDate(task.finished_at)}</p>
                    <details>
                      <summary className="cursor-pointer">Args</summary>
                      <div className="text-xs text-gray-600 overflow-x-auto">
                        {renderJson(task.args)}
                      </div>
                    </details>
                    <details>
                      <summary className="cursor-pointer">Result</summary>
                      <div className="text-xs text-gray-600 overflow-x-auto">
                        {renderJson(task.result)}
                      </div>
                    </details>
                  </div>
                </div>
              ))}
            </div>

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
                disabled={startPipelineMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {startPipelineMutation.isPending ? '시작 중...' : '파이프라인 시작'}
              </button>
            </div>

            <div className="bg-gray-100 p-3 rounded text-xs font-mono overflow-x-auto">
              <div className="text-gray-600">curl 명령어:</div>
              <div className="mt-1">
                curl -X POST "http://localhost:8000/api/v1/pipelines/ai-pipeline" \<br />
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
                curl "http://localhost:8000/api/v1/pipelines/ai-pipeline/&#123;pipeline_id&#125;/status"
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
