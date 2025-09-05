import React, { useState } from 'react';
import type { PipelineStatusResponse } from '../../types';
import { TaskCard } from './TaskCard';

interface TaskGroupProps {
  pipeline: PipelineStatusResponse;
}

export const TaskGroup: React.FC<TaskGroupProps> = ({
  pipeline,
}) => {

  const [collapsedPipelines, setCollapsedPipelines] = useState<Set<string>>(new Set());

  const getStatusBadge = (status: string) => {
    const statusColors = {
      SUCCESS: 'bg-green-100 text-green-800',
      FAILURE: 'bg-red-100 text-red-800',
      PENDING: 'bg-yellow-100 text-yellow-800',
      REVOKED: 'bg-gray-100 text-gray-800'
    };
    return statusColors[status as keyof typeof statusColors] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const togglePipelineCollapse = (pipelineId: string) => {
    setCollapsedPipelines(prev => {
      const newSet = new Set(prev);
      if (newSet.has(pipelineId)) {
        newSet.delete(pipelineId);
      } else {
        newSet.add(pipelineId);
      }
      return newSet;
    });
  };

  return (
    <>

      <div key={pipeline.pipeline_id} className="p-6">
        {/* 파이프라인 헤더 */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => togglePipelineCollapse(pipeline.pipeline_id)}
              className="flex items-center text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg
                className={`w-5 h-5 transition-transform ${collapsedPipelines.has(pipeline.pipeline_id) ? 'rotate-0' : 'rotate-90'}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
            <h4 className="text-lg font-semibold">파이프라인: {pipeline.pipeline_id}</h4>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(pipeline.overall_state)}`}>
              {pipeline.overall_state}
            </span>
          </div>
          <div className="text-sm text-gray-500">
            {formatDate(pipeline.start_time)}
          </div>
        </div>

        {/* 파이프라인 진행률 - 항상 표시 */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>진행률: {pipeline.current_stage}/{pipeline.total_steps} 단계</span>
            <span>{Math.round((pipeline.current_stage / pipeline.total_steps) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(pipeline.current_stage / pipeline.total_steps) * 100}%` }}
            />
          </div>
        </div>

        {/* 태스크 목록 - 접혀있지 않을 때만 표시 */}
        {collapsedPipelines.has(pipeline.pipeline_id) && (
          <div className="space-y-2">
            {pipeline.tasks.map((task) => (
              <TaskCard task={task} getStatusBadge={getStatusBadge} />
            ))}
          </div>
        )}
      </div>
    </>
  );
};