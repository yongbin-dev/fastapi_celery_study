import React, { useState } from 'react';

interface ExecutionCompareInputProps {
  onCompare: (executionId1: string, executionId2: string) => void;
  isLoading?: boolean;
}

export const ExecutionCompareInput: React.FC<ExecutionCompareInputProps> = ({
  onCompare,
  isLoading = false,
}) => {
  const [executionId1, setExecutionId1] = useState('');
  const [executionId2, setExecutionId2] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (executionId1.trim() && executionId2.trim()) {
      onCompare(executionId1.trim(), executionId2.trim());
    }
  };

  const isValid = executionId1.trim() && executionId2.trim();

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">
        Execution 비교
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="execution-id-1"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Execution ID 1
            </label>
            <input
              id="execution-id-1"
              type="text"
              value={executionId1}
              onChange={(e) => setExecutionId1(e.target.value)}
              placeholder="첫 번째 execution ID 입력"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
              disabled={isLoading}
            />
          </div>
          <div>
            <label
              htmlFor="execution-id-2"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Execution ID 2
            </label>
            <input
              id="execution-id-2"
              type="text"
              value={executionId2}
              onChange={(e) => setExecutionId2(e.target.value)}
              placeholder="두 번째 execution ID 입력"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
              disabled={isLoading}
            />
          </div>
        </div>
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!isValid || isLoading}
            className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? '비교 중...' : '비교하기'}
          </button>
        </div>
      </form>
    </div>
  );
};
