import React, { useState, useMemo } from 'react';
import { formatDate } from '@/shared/utils';
import type { ChainExecutionResponseDto } from '../../types/pipeline';
import { TaskGroup } from './TaskGroup';

interface BatchGroupProps {
  batchId: number;
  batchName: string;
  chains: ChainExecutionResponseDto[];
}

export const BatchGroup: React.FC<BatchGroupProps> = ({ batchId, batchName, chains }) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(true);

  const batchStatus = useMemo(() => {
    if (chains.some(chain => chain.status === 'FAILURE')) return 'FAILURE';
    if (chains.some(chain => chain.status === 'PROGRESS')) return 'PROGRESS';
    if (chains.every(chain => chain.status === 'SUCCESS')) return 'SUCCESS';
    if (chains.some(chain => chain.status === 'REVOKED')) return 'REVOKED';
    return 'PENDING';
  }, [chains]);

  const batchProgress = useMemo(() => {
    const totalTasks = chains.reduce((sum, chain) => sum + chain.total_tasks, 0);
    const completedTasks = chains.reduce((sum, chain) => sum + chain.completed_tasks, 0);
    return totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;
  }, [chains]);

  const totalTasksCount = useMemo(() => {
    return chains.reduce((sum, chain) => sum + chain.total_tasks, 0);
  }, [chains]);

  const completedTasksCount = useMemo(() => {
    return chains.reduce((sum, chain) => sum + chain.completed_tasks, 0);
  }, [chains]);

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

  const latestCreatedAt = useMemo(() => {
    if (chains.length === 0) return '';
    return chains.reduce((latest, chain) => {
      return new Date(chain.created_at) > new Date(latest) ? chain.created_at : latest;
    }, chains[0].created_at);
  }, [chains]);

  return (
    <div className="p-6 bg-gray-50">
      {/* Batch �T */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={toggleCollapse}
            className="flex items-center text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg
              className={`w-6 h-6 transition-transform ${isCollapsed ? 'transform -rotate-90' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <div className="flex items-center space-x-2">
            <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <h3 className="text-xl font-bold text-gray-900">
              Batch: {batchName || `Batch #${batchId}`}
            </h3>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadge(batchStatus)}`}>
            {batchStatus}
          </span>
          <span className="text-sm text-gray-500 font-medium">
            ({chains.length} chains)
          </span>
        </div>
        <div className="text-sm text-gray-500">
          {formatDate(latestCreatedAt)}
        </div>
      </div>

      <div className="mb-4 bg-white rounded-lg p-4 border border-gray-200">
        <div className="flex justify-between text-sm text-gray-700 font-medium mb-2">
          <span>Chain : {completedTasksCount} / {totalTasksCount} tasks</span>
          <span>{Math.round(batchProgress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-300 ${
              batchStatus === 'FAILURE' ? 'bg-red-500' :
              batchStatus === 'SUCCESS' ? 'bg-green-500' :
              batchStatus === 'PROGRESS' ? 'bg-blue-500' :
              'bg-yellow-500'
            }`}
            style={{ width: `${Math.round(batchProgress)}%` }}
          />
        </div>
      </div>

      {!isCollapsed && (
        <div className="space-y-4">
          {chains.map((chain) => (
            <div key={chain.id} className="bg-white rounded-lg border border-gray-200 shadow-sm">
              <TaskGroup pipeline={chain} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
