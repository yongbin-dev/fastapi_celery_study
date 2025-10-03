import React, { useState } from 'react';
import type { ChainExecutionResponseDto, Task } from '../../types/pipeline';
import { formatDate } from '@/shared/utils';

interface TaskGroupProps {
  pipeline: ChainExecutionResponseDto;
}

export const TaskGroup: React.FC<TaskGroupProps> = ({ pipeline, }) => {

  const [isCollapsed, setIsCollapsed] = useState<boolean>(true);

  const getStatusBadge = (status: string) => {
    const statusColors: { [key: string]: string } = {
      SUCCESS: 'bg-green-100 text-green-800',
      FAILURE: 'bg-red-100 text-red-800',
      PENDING: 'bg-yellow-100 text-yellow-800',
      PROGRESS: 'bg-blue-100 text-blue-800',
      REVOKED: 'bg-gray-100 text-gray-800'
    };
    return statusColors[status] || 'bg-gray-100 text-gray-800';
  };

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const totalProgress = pipeline.total_tasks > 0 ? (pipeline.completed_tasks / pipeline.total_tasks) * 100 : 0;

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
    <div key={pipeline.id} className="p-6">
      {/* 파이프라인 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={toggleCollapse}
            className="flex items-center text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg
              className={`w-5 h-5 transition-transform ${isCollapsed ? 'transform -rotate-90' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <h4 className="text-lg font-semibold">Chain: {pipeline.chain_name} ({pipeline.chain_id})</h4>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(pipeline.status)}`}>
            {pipeline.status}
          </span>
        </div>
        <div className="text-sm text-gray-500">
          {formatDate(pipeline.created_at)}
        </div>
      </div>

      {/* 파이프라인 진행률 - 항상 표시 */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Progress: {pipeline.completed_tasks} / {pipeline.total_tasks} tasks</span>
          <span>{Math.round(totalProgress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${Math.round(totalProgress)}%` }}
          />
        </div>
      </div>

      {!isCollapsed && (
        <div className="space-y-2 pl-10">
          {pipeline.task_logs.map((task: Task) => (
            <div key={task.id} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <span className="text-sm font-semibold">{task.task_name}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(task.status)}`}>
                    {task.status}
                  </span>
                  <span className="text-xs text-gray-500 font-mono">
                    ID: {task.task_id}
                  </span>
                </div>
                <div className="text-sm text-gray-500">
                  {formatDate(task.finished_at)}
                </div>
              </div>

              {task.error && (
                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                  <strong>Error:</strong> {task.error}
                </div>
              )}

              <details className="mt-2">
                <summary className="text-sm font-medium cursor-pointer">Details</summary>
                <div className="mt-2 space-y-2 text-xs text-gray-600 bg-white p-2 rounded">
                  <p><strong>Args:</strong></p>
                  {renderJson(task.args)}
                  <p><strong>Result:</strong></p>
                  {renderJson(task.result)}
                </div>
              </details>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};