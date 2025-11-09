
import React, { useEffect, useState } from 'react';
import { useExtractPdf, usePipelineStatus } from '../hooks';
import { PdfUploadCard } from './management/PdfUploadCard';
import { PipelineListCard } from './management/PipelineListCard';
import { TaskStatusCard } from './management/TaskStatusCard';
import { UsageGuideCard } from './management/UsageGuideCard';
import type { Pipeline } from '../types/pipeline';

interface TaskManagementTabProps {
}

// TODO: API 연동 시 제거 - 테스트용 목 데이터
const mockPipelines: Pipeline[] = [
  {
    id: 'pipeline-001',
    name: 'OCR 처리 파이프라인',
    status: 'RUNNING',
    createdAt: '2025-11-09T10:00:00Z',
    batches: [
      {
        id: 'batch-001',
        name: 'Batch #1 - 문서 전처리',
        status: 'SUCCESS',
        createdAt: '2025-11-09T10:00:00Z',
        tasks: [
          { id: 'task-001', name: 'PDF 로드', status: 'SUCCESS', progress: 100 },
          { id: 'task-002', name: '이미지 추출', status: 'SUCCESS', progress: 100 },
          { id: 'task-003', name: '이미지 정규화', status: 'SUCCESS', progress: 100 },
        ],
      },
      {
        id: 'batch-002',
        name: 'Batch #2 - OCR 실행',
        status: 'RUNNING',
        createdAt: '2025-11-09T10:05:00Z',
        tasks: [
          { id: 'task-004', name: 'OCR 모델 로드', status: 'SUCCESS', progress: 100 },
          { id: 'task-005', name: 'OCR 처리 (1/10)', status: 'RUNNING', progress: 45 },
          { id: 'task-006', name: 'OCR 처리 (2/10)', status: 'PENDING' },
          { id: 'task-007', name: 'OCR 처리 (3/10)', status: 'PENDING' },
        ],
      },
    ],
  },
];

export const TaskManagementTab: React.FC<TaskManagementTabProps> = ({
}) => {
  const [pipelineId] = useState<string>('');
  const [isAutoRefresh, setIsAutoRefresh] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // React Query 훅들
  const extractPdfMutation = useExtractPdf();

  // 파이프라인 상태 조회 (자동 새로고침이 활성화된 경우에만 폴링)
  const {
    data: pipelineStatus,
  } = usePipelineStatus(
    pipelineId,
    isAutoRefresh && !!pipelineId,
    isAutoRefresh ? 2000 : undefined
  );

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      extractPdfMutation.mutate(selectedFile, {
        onSuccess: (data) => {
          alert('PDF 업로드 성공: ' + JSON.stringify(data, null, 2));
        },
        onError: (error) => {
          alert('업로드 실패: ' + error.message);
        }
      });
    }
  };

  // 파이프라인 완료/실패 시 자동 새로고침 중단
  useEffect(() => {
    if (pipelineStatus?.status === 'SUCCESS' || pipelineStatus?.status === 'FAILURE') {
      setIsAutoRefresh(false);
    }
  }, [pipelineStatus]);


  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="text-center">
        <h2 className="text-2xl font-semibold mb-2">태스크 관리</h2>
        <p className="text-gray-600">AI 파이프라인 API 테스트 및 태스크 관리</p>
      </div>

      {/* AI 파이프라인 API 테스트 */}
      <div className="p-6 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-4">AI 파이프라인 API 테스트</h3>

        <TaskStatusCard pipelineId={pipelineId} pipelineStatus={pipelineStatus} />

        <div className="space-y-6">

          <PdfUploadCard
            selectedFile={selectedFile}
            onFileChange={handleFileChange}
            onUpload={handleUpload}
            extractPdfMutation={extractPdfMutation}
          />

          <PipelineListCard
            pipelines={mockPipelines}
          />

          <UsageGuideCard />
        </div>
      </div>
    </div>
  );
};
