import React, { useState } from 'react';
import { useHistoryTasks } from '../hooks';
import type { TaskHistoryRequest, } from '../types';

export const TaskHistoryTab: React.FC = () => {
  const [searchParams, setSearchParams] = useState<TaskHistoryRequest>({
    hours: 1,
    status: '',
    task_name: '',
    limit: 10
  });
  const [expandedResults, setExpandedResults] = useState<Set<string>>(new Set());

  const { data, isLoading, refetch } = useHistoryTasks(searchParams);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        <div className="text-lg text-gray-600">태스크 이력을 불러오는 중...</div>
        <div className="text-sm text-gray-400 mt-2">잠시만 기다려 주세요</div>
      </div>
    );
  }

  if (!data) {
    return <></>
  }

  const tasks = data.tasks || [];
  const statistics = data.statistics;

  const getStatusBadge = (status: string) => {
    const statusColors = {
      SUCCESS: 'bg-green-100 text-green-800',
      FAILURE: 'bg-red-100 text-red-800',
      PENDING: 'bg-yellow-100 text-yellow-800',
      REVOKED: 'bg-gray-100 text-gray-800'
    };
    return statusColors[status as keyof typeof statusColors] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getTaskDisplayName = (taskName: string) => {
    const taskNames = {
      'app.tasks.example_task': '예제 태스크',
      'app.tasks.simple_task': '간단 태스크',
      'app.tasks.long_running_task': '긴 태스크',
      'app.tasks.ai_task': 'AI 태스크',
      'app.tasks.email_task': '이메일 태스크',
      'Unknown': '알 수 없음'
    };
    return taskNames[taskName as keyof typeof taskNames] || taskName;
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

  const shouldShowExpandButton = (result: any) => {
    if (!result) return false;
    const resultString = typeof result === 'string' ? result : JSON.stringify(result);
    return resultString.length > 100;
  };

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
    setTimeout(() => refetch(), 100);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-lg text-gray-500">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 검색 필터 섹션 */}
      <div className="bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold mb-4">검색 필터</h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          {/* 시간 범위 */}
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

          {/* 상태 필터 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              상태
            </label>
            <select
              value={searchParams.status}
              onChange={(e) => handleSearchChange('status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">전체</option>
              <option value="SUCCESS">성공</option>
              <option value="FAILURE">실패</option>
              <option value="PENDING">대기</option>
              <option value="PROGRESS">진행중</option>
              <option value="REVOKED">취소됨</option>
            </select>
          </div>

          {/* 태스크 이름 필터 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              태스크 이름
            </label>
            <select
              value={searchParams.task_name}
              onChange={(e) => handleSearchChange('task_name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">전체</option>
              <option value="app.tasks.example_task">예제 태스크</option>
              <option value="app.tasks.simple_task">간단 태스크</option>
              <option value="app.tasks.long_running_task">긴 태스크</option>
              <option value="app.tasks.ai_task">AI 태스크</option>
              <option value="app.tasks.email_task">이메일 태스크</option>
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

        {/* 버튼들 */}
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

      {/* 통계 섹션 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-4 rounded-lg border">
            <div className="text-2xl font-bold text-blue-600">{statistics.total_found}</div>
            <div className="text-sm text-gray-500">총 태스크</div>
          </div>
          <div className="bg-white p-4 rounded-lg border">
            <div className="text-2xl font-bold text-green-600">{statistics.by_status?.SUCCESS || 0}</div>
            <div className="text-sm text-gray-500">성공</div>
          </div>
          <div className="bg-white p-4 rounded-lg border">
            <div className="text-2xl font-bold text-red-600">{statistics.by_status?.FAILURE || 0}</div>
            <div className="text-sm text-gray-500">실패</div>
          </div>
          <div className="bg-white p-4 rounded-lg border">
            <div className="text-2xl font-bold text-yellow-600">{statistics.current_active?.active_tasks || 0}</div>
            <div className="text-sm text-gray-500">실행 중</div>
          </div>
        </div>
      )}

      {/* 태스크 목록 */}
      <div className="bg-white rounded-lg border">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold">태스크 이력</h3>
          <p className="text-sm text-gray-500">최근 1시간 내 실행된 태스크 목록</p>
        </div>

        {tasks.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">표시할 태스크 이력이 없습니다.</p>
          </div>
        ) : (
          <div className="divide-y">
            {tasks.map((task: any) => (
              <div key={task.task_id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(task.status)}`}>
                      {task.status}
                    </span>
                    <h4 className="font-medium text-gray-900">
                      {getTaskDisplayName(task.task_name)}
                    </h4>
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatDate(task.date_done)}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Task ID:</span>
                    <span className="ml-2 font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                      {task.task_id}
                    </span>
                  </div>

                  {task.result && (
                    <div className="col-span-full">
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
                </div>

                {task.traceback && (
                  <div className="mt-2 p-2 bg-red-50 rounded text-sm">
                    <span className="font-medium text-red-700">에러:</span>
                    <pre className="text-red-600 whitespace-pre-wrap text-xs mt-1">
                      {task.traceback}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 태스크 타입별 통계 */}
      {statistics?.by_task_type && Object.keys(statistics.by_task_type).length > 0 && (
        <div className="bg-white rounded-lg border">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold">태스크 타입별 통계</h3>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {Object.entries(statistics.by_task_type).map(([taskType, count]) => (
                <div key={taskType} className="flex items-center justify-between">
                  <span className="text-gray-700">{getTaskDisplayName(taskType)}</span>
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm font-medium">
                    {count as number}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};