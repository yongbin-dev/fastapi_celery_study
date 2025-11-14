import { formatDate } from '@/shared/utils';
import React, { useState } from 'react';
import type { ChainExecutionResponseDto } from '../../types/pipeline';

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

  const totalTasks = pipeline.task_logs.length;
  const completedTasks = pipeline.task_logs.filter(log => log.status === 'SUCCESS').length;
  const totalProgress = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

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
          <h4 className="text-lg font-semibold">Execution ID: {pipeline.id}</h4>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(pipeline.status)}`}>
            {pipeline.status}
          </span>
        </div>
        <div className="text-sm text-gray-500">
          {formatDate(pipeline.started_at)} ~ {formatDate(pipeline.finished_at || '')}
        </div>
      </div>

      {/* 메타 정보 */}
      <div className="mb-4 space-y-1 text-sm text-gray-600">
        <div className="flex items-center space-x-2">
          <span className="font-medium">Batch ID:</span>
          <span className="font-mono text-xs">{pipeline.batch_id}</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="font-medium">Initiated by:</span>
          <span>{pipeline.initiated_by}</span>
        </div>
        {Object.keys(pipeline.input_data).length > 0 && (
          <div className="flex items-start space-x-2">
            <span className="font-medium">Input Data:</span>
            <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
              {JSON.stringify(pipeline.input_data)}
            </span>
          </div>
        )}
      </div>

      {/* 파이프라인 진행률 - 항상 표시 */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Progress: {completedTasks} / {totalTasks} tasks</span>
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
        <div className="pl-10">
          <div className="flow-root">
            <ul className="-mb-8">
              {pipeline.task_logs.map((task, taskIdx) => (
                <li key={task.id}>
                  <div className="relative pb-8">
                    {taskIdx !== pipeline.task_logs.length - 1 ? (
                      <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                    ) : null}
                    <div className="relative flex space-x-3">
                      <div>
                        <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${task.status === 'SUCCESS' ? 'bg-green-500' :
                          task.status === 'FAILURE' ? 'bg-red-500' :
                            'bg-blue-500'
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
                          <p>Finish: {task.finished_at ? formatDate(task.finished_at) : 'N/A'}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};