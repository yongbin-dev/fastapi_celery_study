import React, { useState } from 'react';
import type { BatchStatusResponse } from '../../types/pipeline';
import type { UseMutationResult } from '@tanstack/react-query';

interface PipelineListCardProps {
  batchStatus?: BatchStatusResponse;
  isLoading?: boolean;
  cancelPdfMutation: UseMutationResult<void, Error, string, any>
;
}

// 상태 배지 컴포넌트
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  // status에 따라 색상 결정 (completed, failed, running 등)
  const getStatusColor = (status: string) => {
    const lowerStatus = status.toLowerCase();
    if (lowerStatus.includes('completed') || lowerStatus.includes('success')) {
      return 'bg-green-100 text-green-700';
    }
    if (lowerStatus.includes('failed') || lowerStatus.includes('failure') || lowerStatus.includes('error')) {
      return 'bg-red-100 text-red-700';
    }
    if (lowerStatus.includes('running') || lowerStatus.includes('processing')) {
      return 'bg-blue-100 text-blue-700';
    }
    if (lowerStatus.includes('pending') || lowerStatus.includes('waiting')) {
      return 'bg-gray-100 text-gray-700';
    }
    if (lowerStatus.includes('cancelled')) {
      return 'bg-orange-100 text-orange-700';
    }
    return 'bg-gray-100 text-gray-700';
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(status)}`}>
      {status}
    </span>
  );
};

export const PipelineListCard: React.FC<PipelineListCardProps> = ({
  batchStatus,
  isLoading = false,
  cancelPdfMutation
}) => {
  const [selectedContexts, setSelectedContexts] = useState<Set<string>>(new Set());

  // 체크박스 토글
  const toggleContextSelection = (chainId: string) => {
    setSelectedContexts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(chainId)) {
        newSet.delete(chainId);
      } else {
        newSet.add(chainId);
      }
      return newSet;
    });
  };

  // 전체 선택/해제
  const toggleAllSelection = () => {
    if (!batchStatus?.contexts) return;

    const allChainIds = batchStatus.contexts.map(ctx => ctx.chain_execution_id);
    setSelectedContexts(prev => {
      if (prev.size === allChainIds.length) {
        return new Set();
      }
      return new Set(allChainIds);
    });
  };

  // 선택된 Context 취소 핸들러
  const handleCancelSelectedContexts = () => {
    if (selectedContexts.size === 0) {
      alert('취소할 작업을 선택해주세요.');
      return;
    }
// /cancel/{chain_execution_id}
    const confirmed = window.confirm(`선택한 ${selectedContexts.size}개의 작업을 취소하시겠습니까?`);
    if (confirmed) {
      Array.from(selectedContexts).forEach(id => cancelPdfMutation.mutate(id))
      // TODO: API 호출
      setSelectedContexts(new Set());
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex items-center mb-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold mr-3">
          2
        </div>
        <h4 className="font-semibold text-gray-800">배치 작업 목록</h4>
      </div>
      <p className="text-sm text-gray-600 mb-4 ml-11">실행 중인 배치 작업을 확인하고 관리합니다.</p>

      <div className="ml-11 space-y-4">
        {/* 로딩 중 */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block relative">
              <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
            </div>
            <p className="mt-4 text-sm text-gray-600 font-medium">배치 작업을 준비하고 있습니다...</p>
            <p className="mt-2 text-xs text-gray-500">잠시만 기다려 주세요</p>
          </div>
        ) : !batchStatus || !batchStatus.contexts || batchStatus.contexts.length === 0 ? (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="mt-4 text-sm text-gray-500">실행 중인 배치 작업이 없습니다.</p>
          </div>
        ) : (
          <>
            {/* 상단 액션 바 */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-600">
                  {selectedContexts.size > 0 ? (
                    <span className="text-blue-600 font-medium">{selectedContexts.size}개 선택됨</span>
                  ) : (
                    <span>작업을 선택하세요</span>
                  )}
                </span>
              </div>
              <button
                onClick={toggleAllSelection}
                className="text-sm text-gray-600 hover:text-gray-900 font-medium"
              >
                {selectedContexts.size === batchStatus.contexts.length ? '전체 해제' : '전체 선택'}
              </button>
            </div>

            {/* 배치 정보 */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              {/* 배치 헤더 */}
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                    <div>
                      <h6 className="font-semibold text-gray-900">배치 작업</h6>
                      <p className="text-xs text-gray-500">ID: {batchStatus.batch_id}</p>
                      <p className="text-xs text-gray-500">총 {batchStatus.total_count}개 작업</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Context 목록 */}
              <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
                {batchStatus.contexts.map((context) => (
                  <div
                    key={context.chain_execution_id}
                    className="flex items-center space-x-3 p-4 bg-white hover:bg-gray-50 transition-colors"
                  >
                    {/* Context 체크박스 */}
                    <input
                      type="checkbox"
                      checked={selectedContexts.has(context.chain_execution_id)}
                      onChange={() => toggleContextSelection(context.chain_execution_id)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />

                    <div className="flex-1 min-w-0 space-y-3">
                      {/* 헤더: Chain ID, Status, Stage */}
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-medium text-gray-900 truncate">
                              Chain ID: {context.chain_execution_id}
                            </span>
                            {context.is_batch && (
                              <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-purple-100 text-purple-700">
                                배치
                              </span>
                            )}
                          </div>
                          <div className="flex items-center space-x-2 mt-1">
                            <p className="text-xs text-gray-500">
                              Stage: {context.current_stage || 'N/A'}
                            </p>
                            {context.retry_count > 0 && (
                              <span className="text-xs text-orange-600">
                                (재시도: {context.retry_count}회)
                              </span>
                            )}
                          </div>
                        </div>
                        <StatusBadge status={context.status} />
                      </div>

                      {/* 에러 메시지 */}
                      {context.error && (
                        <div className="bg-red-50 border border-red-200 rounded p-2">
                          <p className="text-xs text-red-700 flex items-start space-x-1">
                            <svg className="h-3 w-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                            <span>{context.error}</span>
                          </p>
                        </div>
                      )}

                      {/* 이미지 갤러리 (다중 이미지) */}
                      {context.is_batch && context.public_file_paths && context.public_file_paths.length > 0 ? (
                        <div className="space-y-2">
                          <p className="text-xs text-gray-600 font-medium">
                            이미지 ({context.public_file_paths.length}개)
                          </p>
                          <div className="grid grid-cols-5 gap-2">
                            {context.public_file_paths.map((url, idx) => (
                              <a
                                key={idx}
                                href={url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="group relative aspect-square rounded border border-gray-200 overflow-hidden hover:border-blue-400 transition-colors"
                              >
                                <img
                                  src={url}
                                  alt={`Page ${idx + 1}`}
                                  className="w-full h-full object-cover"
                                />
                                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-opacity flex items-center justify-center">
                                  <span className="text-white text-xs opacity-0 group-hover:opacity-100">
                                    {idx + 1}
                                  </span>
                                </div>
                              </a>
                            ))}
                          </div>
                        </div>
                      ) : context.public_file_path ? (
                        <div className="mt-2">
                          <a
                            href={context.public_file_path}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:text-blue-800 hover:underline flex items-center space-x-1"
                          >
                            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            <span>이미지 보기</span>
                          </a>
                        </div>
                      ) : null}

                      {/* OCR 결과 요약 */}
                      {context.is_batch && context.ocr_results && context.ocr_results.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-xs text-gray-600 font-medium">
                            OCR 결과 ({context.ocr_results.length}개)
                          </p>
                          <div className="space-y-1">
                            {context.ocr_results.map((result, idx) => {
                              const statusColor = 'bg-gray-50 text-gray-700 border-gray-200';

                              return (
                                <details key={idx} className={`border rounded p-2 ${statusColor}`}>
                                  <summary className="text-xs cursor-pointer flex items-center justify-between">
                                    <span>페이지 {idx + 1}: </span>
                                    {result.textBoxes.length > 0 && (
                                      <span className="text-xs opacity-70">
                                        {result.textBoxes.length}개 텍스트
                                      </span>
                                    )}
                                  </summary>
                                  {result.textBoxes.length > 0 && (
                                    <div className="mt-2 space-y-1 pl-3">
                                      {result.textBoxes.map((box, boxIdx) => (
                                        <div key={boxIdx} className="text-xs">
                                          <span className="font-mono bg-white px-1 py-0.5 rounded">
                                            {box.text}
                                          </span>
                                          <span className="ml-2 text-gray-500">
                                            ({(box.confidence * 100).toFixed(1)}%)
                                          </span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </details>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* 시간 정보 */}
                      <div className="flex items-center space-x-3 text-xs text-gray-500">
                        <span>생성: {new Date(context.created_at).toLocaleString('ko-KR')}</span>
                        {context.updated_at && (
                          <span>수정: {new Date(context.updated_at).toLocaleString('ko-KR')}</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 선택된 작업 취소 버튼 */}
            <button
              onClick={handleCancelSelectedContexts}
              disabled={selectedContexts.size === 0}
              className="w-full px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white font-medium rounded-lg hover:from-red-700 hover:to-red-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md flex items-center justify-center space-x-2"
            >
              {selectedContexts.size === 0 ? (
                <>
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span>작업 취소</span>
                </>
              ) : (
                <>
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span>선택한 작업 취소 ({selectedContexts.size}개)</span>
                </>
              )}
            </button>
          </>
        )}
      </div>
    </div>
  );
};
