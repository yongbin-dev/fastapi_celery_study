import React from 'react';
import type { TaskInfoResponse } from '../../types';
import { TaskCard } from './TaskCard';

interface TaskGroupProps {
  rootId: string;
  taskGroup: TaskInfoResponse[];
  isCollapsed: boolean;
  onToggleCollapse: (groupId: string) => void;
  getStatusBadge: (status: string) => string;
  formatDate: (dateString: string) => string;
}

export const TaskGroup: React.FC<TaskGroupProps> = ({
  rootId,
  taskGroup,
  isCollapsed,
  onToggleCollapse,
  getStatusBadge,
  formatDate
}) => {
  return (
    <div className="p-6">
      {/* 그룹 헤더 */}
      <div
        className="mb-4 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={() => onToggleCollapse(rootId)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button className="flex items-center justify-center w-6 h-6 text-gray-500 hover:text-gray-700">
              {isCollapsed ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              )}
            </button>
            <h3 className="font-semibold text-gray-900">
              {taskGroup.length > 1 ? '태스크 체인' : '단일 태스크'}
            </h3>
            <span className="text-sm text-gray-500">
              Root ID: <span className="font-mono">{rootId}</span>
            </span>
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
              {taskGroup.length}개 태스크
            </span>
            {isCollapsed && (
              <div className="flex items-center space-x-2 text-xs">
                {taskGroup.filter(t => t.status === 'SUCCESS').length > 0 && (
                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded">
                    성공 {taskGroup.filter(t => t.status === 'SUCCESS').length}
                  </span>
                )}
                {taskGroup.filter(t => t.status === 'FAILURE').length > 0 && (
                  <span className="px-2 py-1 bg-red-100 text-red-700 rounded">
                    실패 {taskGroup.filter(t => t.status === 'FAILURE').length}
                  </span>
                )}
                {taskGroup.filter(t => t.status === 'PENDING').length > 0 && (
                  <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded">
                    대기 {taskGroup.filter(t => t.status === 'PENDING').length}
                  </span>
                )}
              </div>
            )}
          </div>
          <div className="text-sm text-gray-500">
            {formatDate(taskGroup[0]?.task_time)}
          </div>
        </div>
      </div>

      {/* 태스크 목록 */}
      {!isCollapsed && (
        <div className="space-y-4 ml-4">
          {taskGroup.map((task) => (
            <TaskCard
              key={task.task_id}
              task={task}
              getStatusBadge={getStatusBadge}
              formatDate={formatDate}
            />
          ))}
        </div>
      )}
    </div>
  );
};