import React, { useState } from 'react';
import type { Pipeline } from '../../types/pipeline';

interface PipelineListCardProps {
  // TODO: API 연동 시 실제 데이터로 대체
  pipelines?: Pipeline[];
}

// 상태 배지 컴포넌트
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const colors = {
    PENDING: 'bg-gray-100 text-gray-700',
    RUNNING: 'bg-blue-100 text-blue-700',
    SUCCESS: 'bg-green-100 text-green-700',
    FAILURE: 'bg-red-100 text-red-700',
    CANCELLED: 'bg-orange-100 text-orange-700',
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-700'}`}>
      {status}
    </span>
  );
};

export const PipelineListCard: React.FC<PipelineListCardProps> = ({
  pipelines = [],
}) => {
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());
  const [expandedBatches, setExpandedBatches] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'running' | 'all'>('running');

  // 탭별로 파이프라인 필터링
  const filteredPipelines = activeTab === 'running'
    ? pipelines.filter(p => p.status === 'RUNNING' || p.status === 'PENDING')
    : pipelines;

  // 체크박스 토글
  const toggleTaskSelection = (taskId: string) => {
    setSelectedTasks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };

  // Batch 전체 선택/해제
  const toggleBatchSelection = (batchId: string, taskIds: string[]) => {
    setSelectedTasks(prev => {
      const newSet = new Set(prev);
      const allSelected = taskIds.every(id => newSet.has(id));

      if (allSelected) {
        taskIds.forEach(id => newSet.delete(id));
      } else {
        taskIds.forEach(id => newSet.add(id));
      }
      return newSet;
    });
  };

  // 전체 선택/해제
  const toggleAllSelection = () => {
    const allTaskIds: string[] = [];
    filteredPipelines.forEach(pipeline => {
      pipeline.batches.forEach(batch => {
        batch.tasks.forEach(task => {
          allTaskIds.push(task.id);
        });
      });
    });

    setSelectedTasks(prev => {
      if (prev.size === allTaskIds.length) {
        return new Set();
      }
      return new Set(allTaskIds);
    });
  };

  // Batch 확장/축소 토글
  const toggleBatchExpand = (batchId: string) => {
    setExpandedBatches(prev => {
      const newSet = new Set(prev);
      if (newSet.has(batchId)) {
        newSet.delete(batchId);
      } else {
        newSet.add(batchId);
      }
      return newSet;
    });
  };

  // 선택된 Task 취소 핸들러 (TODO: API 연동)
  const handleCancelSelectedTasks = () => {
    if (selectedTasks.size === 0) {
      alert('취소할 Task를 선택해주세요.');
      return;
    }

    const confirmed = window.confirm(`선택한 ${selectedTasks.size}개의 Task를 취소하시겠습니까?`);
    if (confirmed) {
      console.log('취소할 Task IDs:', Array.from(selectedTasks));
      // TODO: API 호출
      alert(`${selectedTasks.size}개의 Task 취소 요청이 전송되었습니다. (API 연동 예정)`);
      setSelectedTasks(new Set());
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex items-center mb-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold mr-3">
          2
        </div>
        <h4 className="font-semibold text-gray-800">파이프라인 목록</h4>
      </div>
      <p className="text-sm text-gray-600 mb-4 ml-11">실행 중인 파이프라인을 확인하고 Task를 관리합니다.</p>

      <div className="ml-11 space-y-4">
        {/* 탭 메뉴 */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('running')}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all ${
              activeTab === 'running'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center justify-center space-x-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>실행중</span>
              <span className="bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full text-xs">
                {pipelines.filter(p => p.status === 'RUNNING' || p.status === 'PENDING').length}
              </span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all ${
              activeTab === 'all'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center justify-center space-x-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
              <span>전체</span>
              <span className="bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full text-xs">
                {pipelines.length}
              </span>
            </div>
          </button>
        </div>

        {/* 파이프라인이 없는 경우 */}
        {filteredPipelines.length === 0 ? (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="mt-4 text-sm text-gray-500">
              {activeTab === 'running' ? '실행 중인 파이프라인이 없습니다.' : '파이프라인이 없습니다.'}
            </p>
          </div>
        ) : (
          <>
            {/* 상단 액션 바 */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-600">
                  {selectedTasks.size > 0 ? (
                    <span className="text-blue-600 font-medium">{selectedTasks.size}개 선택됨</span>
                  ) : (
                    <span>Task를 선택하세요</span>
                  )}
                </span>
              </div>
              <button
                onClick={toggleAllSelection}
                className="text-sm text-gray-600 hover:text-gray-900 font-medium"
              >
                {selectedTasks.size === filteredPipelines.reduce((acc, p) => acc + p.batches.reduce((b, batch) => b + batch.tasks.length, 0), 0)
                  ? '전체 해제'
                  : '전체 선택'}
              </button>
            </div>

            {/* 파이프라인 목록 */}
            <div className="space-y-4 max-h-[600px] overflow-y-auto mb-4">
              {filteredPipelines.map(pipeline => (
                <div key={pipeline.id} className="border border-gray-200 rounded-lg overflow-hidden">
                  {/* 파이프라인 헤더 */}
                  <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <div>
                          <h6 className="font-semibold text-gray-900">{pipeline.name}</h6>
                          <p className="text-xs text-gray-500">ID: {pipeline.id}</p>
                        </div>
                      </div>
                      <StatusBadge status={pipeline.status} />
                    </div>
                  </div>

                  {/* Batch 목록 */}
                  <div className="divide-y divide-gray-200">
                    {pipeline.batches.map(batch => {
                      const batchTaskIds = batch.tasks.map(t => t.id);
                      const isBatchExpanded = expandedBatches.has(batch.id);
                      const allBatchTasksSelected = batchTaskIds.every(id => selectedTasks.has(id));
                      const someBatchTasksSelected = batchTaskIds.some(id => selectedTasks.has(id)) && !allBatchTasksSelected;

                      return (
                        <div key={batch.id} className="bg-white">
                          {/* Batch 헤더 */}
                          <div className="px-4 py-3 hover:bg-gray-50 transition-colors">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3 flex-1">
                                {/* Batch 전체 선택 체크박스 */}
                                <input
                                  type="checkbox"
                                  checked={allBatchTasksSelected}
                                  ref={input => {
                                    if (input) {
                                      input.indeterminate = someBatchTasksSelected;
                                    }
                                  }}
                                  onChange={() => toggleBatchSelection(batch.id, batchTaskIds)}
                                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                />

                                <button
                                  onClick={() => toggleBatchExpand(batch.id)}
                                  className="flex items-center space-x-2 flex-1 text-left"
                                >
                                  <svg
                                    className={`h-4 w-4 text-gray-500 transition-transform ${isBatchExpanded ? 'rotate-90' : ''}`}
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                  >
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                  </svg>
                                  <div className="flex-1">
                                    <div className="flex items-center space-x-2">
                                      <span className="font-medium text-gray-900">{batch.name}</span>
                                      <span className="text-xs text-gray-500">({batch.tasks.length} Tasks)</span>
                                    </div>
                                    <p className="text-xs text-gray-500">ID: {batch.id}</p>
                                  </div>
                                </button>

                                <StatusBadge status={batch.status} />
                              </div>
                            </div>
                          </div>

                          {/* Task 목록 (확장 시) */}
                          {isBatchExpanded && (
                            <div className="bg-gray-50 px-4 py-2">
                              <div className="space-y-2">
                                {batch.tasks.map(task => (
                                  <div
                                    key={task.id}
                                    className="flex items-center space-x-3 p-3 bg-white rounded border border-gray-200 hover:border-blue-300 transition-colors"
                                  >
                                    {/* Task 체크박스 */}
                                    <input
                                      type="checkbox"
                                      checked={selectedTasks.has(task.id)}
                                      onChange={() => toggleTaskSelection(task.id)}
                                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                    />

                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center space-x-2">
                                        <span className="text-sm font-medium text-gray-900 truncate">{task.name}</span>
                                        {task.progress !== undefined && (
                                          <span className="text-xs text-gray-500">({task.progress}%)</span>
                                        )}
                                      </div>
                                      <p className="text-xs text-gray-500 truncate">ID: {task.id}</p>
                                    </div>

                                    <StatusBadge status={task.status} />
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            {/* 선택된 Task 취소 버튼 - 파이프라인 목록 아래 */}
            <button
              onClick={handleCancelSelectedTasks}
              disabled={selectedTasks.size === 0}
              className="w-full px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white font-medium rounded-lg hover:from-red-700 hover:to-red-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md flex items-center justify-center space-x-2"
            >
              {selectedTasks.size === 0 ? (
                <>
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span>Task 취소</span>
                </>
              ) : (
                <>
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span>선택한 Task 취소 ({selectedTasks.size}개)</span>
                </>
              )}
            </button>
          </>
        )}
      </div>
    </div>
  );
};
