import React, { useState } from 'react';
import type { PipelineStatusResponse } from '../../types';

interface TaskGroupProps {
  pipeline: PipelineStatusResponse;
}

export const TaskGroup: React.FC<TaskGroupProps> = ({
  pipeline,
}) => {

  const [collapsedPipelines, setCollapsedPipelines] = useState<Set<string>>(new Set());
  
  // 배열에서 chain_id를 추출 (모든 스테이지가 같은 chain_id를 가짐)
  const chainId = pipeline.length > 0 ? pipeline[0].chain_id : '';
  
  // 전체 진행률 계산
  const totalProgress = pipeline.length > 0 
    ? Math.round(pipeline.reduce((sum, stage) => sum + stage.progress, 0) / pipeline.length)
    : 0;
  
  // 전체 상태 결정
  const overallStatus = pipeline.every(stage => stage.status === 'SUCCESS') 
    ? 'SUCCESS' 
    : pipeline.some(stage => stage.status === 'FAILURE')
    ? 'FAILURE'
    : pipeline.some(stage => stage.status === 'PROGRESS')
    ? 'PROGRESS'
    : 'PENDING';
    
  // 시작 시간 (가장 이른 created_at 또는 updated_at)
  const startTime = pipeline.length > 0 
    ? Math.min(...pipeline.map(stage => stage.created_at || stage.updated_at))
    : Date.now() / 1000;

  const getStatusBadge = (status: string) => {
    const statusColors = {
      SUCCESS: 'bg-green-100 text-green-800',
      FAILURE: 'bg-red-100 text-red-800',
      PENDING: 'bg-yellow-100 text-yellow-800',
      REVOKED: 'bg-gray-100 text-gray-800'
    };
    return statusColors[status as keyof typeof statusColors] || 'bg-gray-100 text-gray-800';
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
          <span>진행률: {pipeline.length}개 스테이지</span>
          <span>{totalProgress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${totalProgress}%` }}
          />
        </div>
      </div>

      {/* 스테이지 목록 - 접혀있지 않을 때만 표시 */}
      {!collapsedPipelines.has(chainId) && (
        <div className="space-y-2">
          {pipeline.map((stage, index) => (
            <div key={`${stage.chain_id}-${stage.stage}`} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <span className="text-sm font-medium text-gray-600">스테이지 {stage.stage}</span>
                  <span className="text-sm font-semibold">{stage.metadata?.stage_name || `스테이지 ${stage.stage}`}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(stage.status)}`}>
                    {stage.status}
                  </span>
                </div>
                <div className="text-sm text-gray-500">
                  {formatDate(stage.updated_at)}
                </div>
              </div>
              
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>진행률: {stage.progress}%</span>
                <span>실행 시간: {stage.metadata?.execution_time?.toFixed(2) || '0.00'}초</span>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
                <div
                  className="bg-blue-500 h-1 rounded-full transition-all duration-300"
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