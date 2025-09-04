import React, { useState } from 'react';
import type { TaskInfoResponse } from '../../types';

interface TaskCardProps {
  task: TaskInfoResponse;
  getStatusBadge: (status: string) => string;
  formatDate: (dateString: string) => string;
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  getStatusBadge,
  formatDate
}) => {
  const [expandedResults, setExpandedResults] = useState<Set<string>>(new Set());

  const toggleResultExpansion = (taskId: string) => {
    setExpandedResults(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };

  const formatResult = (result: any, taskId: string) => {
    if (!result) return '';
    const resultString = typeof result === 'string' ? result : JSON.stringify(result, null, 2);
    const isExpanded = expandedResults.has(taskId);
    const shouldTruncate = resultString.length > 100;

    if (!shouldTruncate) {
      return resultString;
    }

    return isExpanded ? resultString : resultString.substring(0, 100) + '...';
  };

  const shouldShowExpandButton = (result: any) => {
    if (!result) return false;
    const resultString = typeof result === 'string' ? result : JSON.stringify(result);
    return resultString.length > 100;
  };

  return (
    <div className="p-4 bg-white border rounded-lg hover:bg-gray-50">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-3">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(task.status)}`}>
            {task.status}
          </span>
          <h4 className="font-medium text-gray-900">
            {task.task_name}
          </h4>
          {task.retry_count > 0 && (
            <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">
              재시도 {task.retry_count}회
            </span>
          )}
        </div>
        <div className="text-sm text-gray-500">
          {formatDate(task.task_time)}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-3">
        <div>
          <span className="font-medium text-gray-700">Task ID:</span>
          <span className="ml-2 font-mono text-xs bg-gray-100 px-2 py-1 rounded">
            {task.task_id}
          </span>
        </div>

        {task.completed_time && (
          <div>
            <span className="font-medium text-gray-700">완료 시간:</span>
            <span className="ml-2 text-xs text-gray-600">
              {formatDate(task.completed_time)}
            </span>
          </div>
        )}
      </div>


      {/* Args & Kwargs */}
      {(task.args || task.kwargs) && (
        <div className="mb-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {task.args && (
              <div>
                <span className="font-medium text-gray-700">Args:</span>
                <div className="mt-1">
                  <code className="bg-gray-50 p-2 rounded block font-mono text-xs">
                    {task.args}
                  </code>
                </div>
              </div>
            )}
            {task.kwargs && (
              <div>
                <span className="font-medium text-gray-700">Kwargs:</span>
                <div className="mt-1">
                  <code className="bg-gray-50 p-2 rounded block font-mono text-xs">
                    {task.kwargs}
                  </code>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {task.result && (
        <div className="mb-3">
          <div className="flex items-center justify-between mb-1">
            <span className="font-medium text-gray-700">결과:</span>
            {shouldShowExpandButton(task.result) && (
              <button
                onClick={() => toggleResultExpansion(task.task_id)}
                className="text-xs text-blue-600 hover:text-blue-800 focus:outline-none"
              >
                {expandedResults.has(task.task_id) ? '접기' : '더보기'}
              </button>
            )}
          </div>
          <div className={`text-gray-600 text-sm ${expandedResults.has(task.task_id) ? 'whitespace-pre-wrap' : ''}`}>
            <code className="bg-gray-50 p-2 rounded block font-mono text-xs">
              {formatResult(task.result, task.task_id)}
            </code>
          </div>
        </div>
      )}

      {(task.error_message || task.traceback) && (
        <div className="mt-2 p-2 bg-red-50 rounded text-sm">
          <span className="font-medium text-red-700">에러:</span>
          {task.error_message && (
            <div className="text-red-600 text-sm mt-1">
              <strong>메시지:</strong> {task.error_message}
            </div>
          )}
          {task.traceback && (
            <pre className="text-red-600 whitespace-pre-wrap text-xs mt-1">
              <strong>Traceback:</strong>{'\n'}{task.traceback}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};