import React from 'react';
import type { TaskStatusResponse } from '../types';

interface TaskStatusCardProps {
  taskStatus: TaskStatusResponse;
  onCancel: (taskId: string) => void;
  isCanceling: boolean;
}

export const TaskStatusCard: React.FC<TaskStatusCardProps> = ({
  taskStatus,
  onCancel,
  isCanceling,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-800';
      case 'PROGRESS':
        return 'bg-blue-100 text-blue-800';
      case 'SUCCESS':
        return 'bg-green-100 text-green-800';
      case 'FAILURE':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getProgressPercentage = () => {
    if (taskStatus.total && taskStatus.current) {
      return Math.round((taskStatus.current / taskStatus.total) * 100);
    }
    return 0;
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-md border">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h4 className="text-sm font-medium text-gray-900">태스크 ID</h4>
          <p className="text-xs text-gray-600 font-mono">{taskStatus.task_id}</p>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(taskStatus.status)}`}>
          {taskStatus.status}
        </span>
      </div>

      <div className="mb-3">
        <p className="text-sm text-gray-700">{taskStatus.message}</p>
      </div>

      {taskStatus.status === 'PROGRESS' && taskStatus.current && taskStatus.total && (
        <div className="mb-3">
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>진행률</span>
            <span>{getProgressPercentage()}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${getProgressPercentage()}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {taskStatus.current} / {taskStatus.total}
          </div>
        </div>
      )}

      {taskStatus.result && (
        <div className="mb-3">
          <h5 className="text-sm font-medium text-gray-900 mb-1">결과</h5>
          <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-32">
            {JSON.stringify(taskStatus.result, null, 2)}
          </pre>
        </div>
      )}

      {taskStatus.error && (
        <div className="mb-3">
          <h5 className="text-sm font-medium text-red-900 mb-1">오류</h5>
          <p className="text-xs text-red-700 bg-red-50 p-2 rounded">{taskStatus.error}</p>
        </div>
      )}

      {(taskStatus.status === 'PENDING' || taskStatus.status === 'PROGRESS') && (
        <button
          onClick={() => onCancel(taskStatus.task_id)}
          disabled={isCanceling}
          className="w-full mt-2 bg-red-600 text-white py-1 px-3 text-sm rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCanceling ? '취소 중...' : '태스크 취소'}
        </button>
      )}
    </div>
  );
};