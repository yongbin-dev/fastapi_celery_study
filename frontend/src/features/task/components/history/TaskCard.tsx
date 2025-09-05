import React from 'react';
import type { TaskStatusResponse } from '../../types';

interface TaskCardProps {
  task: TaskStatusResponse;
  getStatusBadge: (status: string) => void
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  getStatusBadge
}) => {
  return (
    <>
      <div key={task.task_id} className="border rounded-lg p-4 bg-gray-50">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-3">
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm font-medium">
              Step {task.step}
            </span>
            <h5 className="font-medium">{task.task_name}</h5>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(task.status)}`}>
              {task.status}
            </span>
          </div>
          <div className="text-sm text-gray-500">
            {task.progress}%
          </div>
        </div>
        {/* 태스크 진행률 바 */}
        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
          <div
            className="bg-green-600 h-1.5 rounded-full transition-all duration-300"
            style={{ width: `${task.progress}%` }}
          />
        </div>

        {task.result && (
          <div className="text-sm text-gray-600 mt-2">
            <strong>결과:</strong> {task.result}
          </div>
        )}

        {task.traceback && (
          <div className="text-sm text-red-600 mt-2">
            <strong>오류:</strong>
            <pre className="mt-1 text-xs bg-red-50 p-2 rounded overflow-x-auto">
              {task.traceback}
            </pre>
          </div>
        )}
      </div>
    </>
  )

};