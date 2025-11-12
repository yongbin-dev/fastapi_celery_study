
import React, { useEffect, useState } from 'react';
import { useBatchPipelineStatus, useCancelPdf, useExtractPdf, usePipelineStatus } from '../hooks';
import { PdfUploadCard } from './management/PdfUploadCard';
import { PipelineListCard } from './management/PipelineListCard';
import { TaskStatusCard } from './management/TaskStatusCard';
import { UsageGuideCard } from './management/UsageGuideCard';

interface TaskManagementTabProps {
}

export const TaskManagementTab: React.FC<TaskManagementTabProps> = ({
}) => {
  const [pipelineId ,] = useState<string>('');

  const [batchId , setBatchId] = useState<string>('');
  const [isAutoRefresh, setIsAutoRefresh] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [shouldPollBatch, setShouldPollBatch] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false); // 수동 로딩 상태 관리

  // React Query 훅들
  const extractPdfMutation = useExtractPdf();
  const cancelPdfMutation = useCancelPdf();

  // 파이프라인 상태 조회 (자동 새로고침이 활성화된 경우에만 폴링)
  const {
    data: pipelineStatus,
  } = usePipelineStatus(
    pipelineId,
    isAutoRefresh && !!pipelineId,
    isAutoRefresh ? 2000 : undefined
  );

  // 배치 상태 조회 (shouldPollBatch가 true일 때만 폴링)
  const {
    data: batchStatus,
  } = useBatchPipelineStatus(
    batchId,
    shouldPollBatch && !!batchId ? 2000 : undefined
  );

  // 배치 데이터 로딩 상태 판단
  // 1. 처리 중이거나
  // 2. PDF 업로드 중이거나
  // 3. batchId는 있지만 batchStatus가 없거나
  // 4. batchStatus는 있지만 total_count가 0 (아직 데이터가 준비되지 않음)
  const isLoadingBatchData =
    isProcessing ||
    extractPdfMutation.isPending 
    // (!!batchId && !batchStatus) ||
    // (!!batchStatus && batchStatus.total_count === 0);

  // 배치 데이터가 실제로 로드되면 처리 상태 종료
  useEffect(() => {
    setIsProcessing(false);

    // if (batchStatus && batchStatus.total_count > 0 && isProcessing) {
    //   setIsProcessing(false);
    // }
  }, [batchStatus, isProcessing]);

  // 디버깅용 로그


  // 배치 작업이 모두 완료되었는지 확인 및 폴링 제어
  useEffect(() => {
    if (!batchStatus?.contexts || batchStatus.contexts.length === 0) {
      return;
    }

    // 모든 context의 status를 확인하여 완료/실패 여부 판단
    const allFinished = batchStatus.contexts.every(context => {
      const status = context.status;
      return status == "SUCCESS"
    });

    if (allFinished && shouldPollBatch) {
      console.log('배치 작업이 모두 완료되어 폴링을 중단합니다.');
      setShouldPollBatch(false);
    }
  }, [batchStatus, shouldPollBatch]);

  const handleFileSelect = (file: File | null) => {
    setSelectedFile(file);
  };

  const handleUpload = () => {
    if (selectedFile) {
      // setIsProcessing(true); // 처리 시작
      extractPdfMutation.mutate(selectedFile, {
        onSuccess: (data) => {
          setBatchId(data.batch_id);
          setShouldPollBatch(true); // 새로운 배치 시작 시 폴링 재시작
        },
        onError: (error) => {
          console.error('PDF 업로드 실패:', error);
          setIsProcessing(false); // 에러 시 처리 상태 종료
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

  useEffect(()=>{
    console.log(batchStatus)
  } , [batchStatus])

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
            onFileSelect={handleFileSelect}
            onUpload={handleUpload}
            isLoading={isLoadingBatchData}
          />

          <PipelineListCard
            batchStatus={batchStatus}
            isLoading={isLoadingBatchData}
            cancelPdfMutation={cancelPdfMutation}
          />

          <UsageGuideCard />
        </div>
      </div>
    </div>
  );
};
