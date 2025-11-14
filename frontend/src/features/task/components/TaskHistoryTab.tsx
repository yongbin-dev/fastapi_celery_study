
import React, { useState, useMemo } from 'react';
import { type TaskHistoryRequest } from '../types';
import { useHistoryTasks } from '../hooks';
import type { ChainExecutionResponseDto } from '../types/pipeline';
import { TaskGroup, BatchGroup } from './history';

export const TaskHistoryTab: React.FC = () => {
  const [searchParams, setSearchParams] = useState<TaskHistoryRequest>({
    hours: 1,
    status: '',
    task_name: '',
    limit: 10
  });

  const { data: pipelines = [], isLoading, refetch } = useHistoryTasks(searchParams);

  // Batch로 그룹핑
  const groupedData = useMemo(() => {
    const batches = new Map<string, ChainExecutionResponseDto[]>();
    const noBatchChains: ChainExecutionResponseDto[] = [];

    pipelines.forEach((pipeline: ChainExecutionResponseDto) => {
      if (pipeline.batch_id) {
        const batchChains = batches.get(pipeline.batch_id) || [];
        batchChains.push(pipeline);
        batches.set(pipeline.batch_id, batchChains);
      } else {
        noBatchChains.push(pipeline);
      }
    });

    return { batches, noBatchChains };
  }, [pipelines]);
  const handleSearchChange = (field: string, value: string | number) => {
    setSearchParams(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSearch = () => {
    refetch();
  };

  const handleReset = () => {
    setSearchParams({
      hours: 1,
      status: '',
      task_name: '',
      limit: 100
    });
    setTimeout(() => refetch(), 200);
  };


  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold mb-4">검색 필터</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              조회 시간 범위 (시간)
            </label>
            <select
              value={searchParams.hours}
              onChange={(e) => handleSearchChange('hours', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value={1}>1시간</option>
              <option value={3}>3시간</option>
              <option value={6}>6시간</option>
              <option value={12}>12시간</option>
              <option value={24}>1일</option>
              <option value={72}>3일</option>
              <option value={168}>1주일</option>
            </select>
          </div>

          {/* 결과 수 제한 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              최대 결과 수
            </label>
            <select
              value={searchParams.limit}
              onChange={(e) => handleSearchChange('limit', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value={10}>10개</option>
              <option value={25}>25개</option>
              <option value={50}>50개</option>
              <option value={100}>100개</option>
              <option value={250}>250개</option>
              <option value={500}>500개</option>
              <option value={1000}>1000개</option>
            </select>
          </div>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={handleSearch}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '검색 중...' : '검색'}
          </button>
          <button
            onClick={handleReset}
            disabled={isLoading}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            초기화
          </button>
        </div>
      </div>


      {/* 태스크 목록 */}
      <div className="bg-white rounded-lg border">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold">태스크 이력</h3>
          <p className="text-sm text-gray-500">최근 {searchParams.hours}시간 내 실행된 파이프라인 목록</p>
        </div>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <div className="text-lg text-gray-600">태스크 이력을 불러오는 중...</div>
            <div className="text-sm text-gray-400 mt-2">잠시만 기다려 주세요</div>
          </div>
        ) : pipelines.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">표시할 파이프라인 이력이 없습니다.</p>
          </div>
        ) : (
          <div className="divide-y">
            {/* Batch가 있는 경우 */}
            {Array.from(groupedData.batches.entries()).map(([batchId, chains]) => (
              <BatchGroup
                key={`batch-${batchId}`}
                batchId={batchId}
                chains={chains}
              />
            ))}

            {/* Batch가 없는 Chain들 */}
            {groupedData.noBatchChains.map((pipeline: ChainExecutionResponseDto) => (
              <TaskGroup
                key={pipeline.id}
                pipeline={pipeline}
              />
            ))}
          </div>
        )}

      </div>


    </div>
  );
};
