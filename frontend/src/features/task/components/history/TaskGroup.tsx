import React, { useState } from 'react';
import type { PipelineStatusResponse } from '../../types';
import { TaskStatus } from '../../types';

interface TaskGroupProps {
  pipeline: PipelineStatusResponse;
}

export const TaskGroup: React.FC<TaskGroupProps> = ({
  pipeline,
}) => {

  const [collapsedPipelines, setCollapsedPipelines] = useState<Set<string>>(new Set());

  // chain_id 추출
  const chainId = pipeline.chain_id;

  // 전체 진행률
  const totalProgress = pipeline.overall_progress;

  // 전체 상태 결정
  const overallStatus = pipeline.stages.every(stage => stage.status === TaskStatus.SUCCESS)
    ? TaskStatus.SUCCESS
    : pipeline.stages.some(stage => stage.status === TaskStatus.FAILURE)
      ? TaskStatus.FAILURE
      : pipeline.stages.some(stage => stage.status === TaskStatus.PROGRESS)
        ? TaskStatus.PROGRESS
        : TaskStatus.PENDING;

  // 시작 시간 (가장 이른 created_at)
  const startTime = pipeline.stages.length > 0
    ? Math.min(...pipeline.stages.map(stage => stage.created_at))
    : Date.now() / 1000;

  const getStatusBadge = (status: TaskStatus) => {
    const statusColors = {
      [TaskStatus.SUCCESS]: 'bg-green-100 text-green-800',
      [TaskStatus.FAILURE]: 'bg-red-100 text-red-800',
      [TaskStatus.PENDING]: 'bg-yellow-100 text-yellow-800',
      [TaskStatus.PROGRESS]: 'bg-blue-100 text-blue-800',
      [TaskStatus.REVOKED]: 'bg-gray-100 text-gray-800'
    };
    return statusColors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (timestamp: number) => {
    if (!timestamp) return '-';
    return new Date(timestamp * 1000).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const togglePipelineCollapse = (chainId: string) => {
    setCollapsedPipelines(prev => {
      const newSet = new Set(prev);
      if (newSet.has(chainId)) {
        newSet.delete(chainId);
      } else {
        newSet.add(chainId);
      }
      return newSet;
    });
  };

  return (
    <div key={chainId} className="p-6">
      {/* 파이프라인 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => togglePipelineCollapse(chainId)}
            className="flex items-center text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg
              className={`w-5 h-5 transition-transform ${collapsedPipelines.has(chainId) ? 'rotate-0' : 'rotate-90'}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <h4 className="text-lg font-semibold">체인: {chainId}</h4>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(overallStatus)}`}>
            {overallStatus}
          </span>
        </div>
        <div className="text-sm text-gray-500">
          {formatDate(startTime)}
        </div>
      </div>

      {/* 파이프라인 진행률 - 항상 표시 */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>진행률: {pipeline.total_stages}개 스테이지 (현재: {pipeline.current_stage || 0})</span>
          <span>{Math.round(totalProgress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${Math.round(totalProgress)}%` }}
          />
        </div>
      </div>

      {collapsedPipelines.has(chainId) && (
        <div className="space-y-2">
          {pipeline.stages.map((stage) => (
            <div key={`${stage.chain_id}-${stage.stage}`} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <span className="text-sm font-medium text-gray-600">스테이지 {stage.stage}</span>
                  <span className="text-sm font-semibold">{stage.stage_name}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(stage.status)}`}>
                    {stage.status}
                  </span>
                  {stage.task_id && (
                    <span className="text-xs text-gray-500 font-mono">
                      ID: {stage.task_id}
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-500">
                  {formatDate(stage.updated_at)}
                </div>
              </div>

              <div className="mb-2">
                <p className="text-sm text-gray-600">{stage.description}</p>
                <p className="text-xs text-gray-500">소요 시간: {(stage.updated_at - stage.created_at).toFixed(2)}초</p>
              </div>

              <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                <span>진행률: {stage.progress}%</span>
                <span>
                  {stage.created_at > 0 ? `시작: ${formatDate(stage.created_at)}` : '대기 중'}
                </span>
              </div>

              {stage.error_message && (
                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                  <strong>오류:</strong> {stage.error_message}
                </div>
              )}

              <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
                <div
                  className={`h-1 rounded-full transition-all duration-300 ${stage.status === TaskStatus.FAILURE ? 'bg-red-500' :
                    stage.status === TaskStatus.SUCCESS ? 'bg-green-500' :
                      'bg-blue-500'
                    }`}
                  style={{ width: `${stage.progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

refactor(fullstack): CRUD 계층 리팩토링 및 파이프라인 UI 개선
백엔드와 프론트엔드 전반에 걸친 대규모 아키텍처 리팩토링을 적용합니다.
  Backend:
- CRUD 계층을 `sync_crud`와 `async_crud` 모듈로 분리하여 동기 및 비동기 데이터베이스 연산을
  모두 지원하도록 재구성했습니다.
- Celery 시그널 핸들러와 파이프라인 서비스가 새로운 `async_crud` 모듈을 사용하도록 업데이트하여
  성능과 일관성을 개선했습니다.
- 더 이상 사용되지 않는 레거시 인증(`security` 디렉토리) 및 의존성 파일들을 제거했습니다.
- `pipeline_service`를 개선하여 개별 스테이지 상태를 포함한 상세한 파이프라인 히스토리를 DB
  기반으로 제공하도록 변경했습니다.

  Frontend:
- `chatbot` 기능과 관련된 모든 컴포넌트, 훅, API 정의를 제거했습니다.
- 기능 제거에 따라 메인 애플리케이션 레이아웃과 네비게이션을 업데이트했습니다.
- Task 히스토리 및 관리 탭을 새로운 백엔드 API(`PipelineStagesResponse`) 응답 형식에 맞춰
리팩토링했습니다.
- `TaskGroup` 컴포넌트를 개선하여 전체 파이프라인 진행률, 개별 스테이지 상태 및 오류 메시지를
  시각화하도록 구현했습니다.