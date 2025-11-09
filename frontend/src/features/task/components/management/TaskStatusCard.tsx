import React from 'react';
import { TaskStatus } from '../../types';

interface PipelineStatus {
  task_id: string;
  status: string;
  message: string;
}

interface TaskStatusCardProps {
  pipelineId: string;
  pipelineStatus?: PipelineStatus;
}

export const TaskStatusCard: React.FC<TaskStatusCardProps> = ({
  pipelineId,
  pipelineStatus,
}) => {
  if (!pipelineId && !pipelineStatus) {
    return null;
  }

  return (
    <>
      {pipelineId && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
          <p className="text-sm text-blue-700">
            <strong>현재 파이프라인 ID:</strong> {pipelineId}
          </p>
        </div>
      )}

      {pipelineStatus && (
        <div className="mb-4 p-4 rounded-lg border-2 transition-all duration-300">
          {/* Pending 상태 */}
          {pipelineStatus.status === TaskStatus.PENDING && (
            <div className="bg-yellow-50 border-yellow-300">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <svg className="animate-spin h-6 w-6 text-yellow-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-yellow-800 mb-1">처리 대기 중</h4>
                  <p className="text-sm text-yellow-700">{pipelineStatus.message}</p>
                  <div className="mt-2 pt-2 border-t border-yellow-200">
                    <p className="text-xs text-yellow-600">
                      <strong>Task ID:</strong> <span className="font-mono">{pipelineStatus.task_id}</span>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Success 상태 */}
          {pipelineStatus.status === TaskStatus.SUCCESS && (
            <div className="bg-green-50 border-green-300">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-green-800 mb-1">처리 완료</h4>
                  <p className="text-sm text-green-700">{pipelineStatus.message}</p>
                  <div className="mt-2 pt-2 border-t border-green-200">
                    <p className="text-xs text-green-600">
                      <strong>Task ID:</strong> <span className="font-mono">{pipelineStatus.task_id}</span>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Failure 상태 */}
          {pipelineStatus.status === TaskStatus.FAILURE && (
            <div className="bg-red-50 border-red-300">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-red-800 mb-1">처리 실패</h4>
                  <p className="text-sm text-red-700">{pipelineStatus.message}</p>
                  <div className="mt-2 pt-2 border-t border-red-200">
                    <p className="text-xs text-red-600">
                      <strong>Task ID:</strong> <span className="font-mono">{pipelineStatus.task_id}</span>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 기타 상태 (진행중 등) */}
          {pipelineStatus.status !== TaskStatus.PENDING &&
           pipelineStatus.status !== TaskStatus.SUCCESS &&
           pipelineStatus.status !== TaskStatus.FAILURE && (
            <div className="bg-blue-50 border-blue-300">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="animate-pulse h-6 w-6 rounded-full bg-blue-600 flex items-center justify-center">
                    <div className="h-3 w-3 rounded-full bg-white"></div>
                  </div>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-blue-800 mb-1">
                    상태: {pipelineStatus.status}
                  </h4>
                  <p className="text-sm text-blue-700">{pipelineStatus.message}</p>
                  <div className="mt-2 pt-2 border-t border-blue-200">
                    <p className="text-xs text-blue-600">
                      <strong>Task ID:</strong> <span className="font-mono">{pipelineStatus.task_id}</span>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
};
