// 태스크 상태 enum
export const TaskStatus = {
  PENDING: 'PENDING',
  PROGRESS: 'PROGRESS',
  SUCCESS: 'SUCCESS',
  FAILURE: 'FAILURE',
  REVOKED: 'REVOKED',
} as const;

export type TaskStatus = (typeof TaskStatus)[keyof typeof TaskStatus];

// 태스크 요청 타입들
export interface TaskHistoryRequest {
  hours: number;
  status: string;
  task_name: string;
  limit: number;
}

// 모델 테스트 관련 타입들
export interface ModelTestRequest {
  image1: File;
  image2: File;
}

export interface ModelTestResponse {
  task_id: string;
  status: string;
  message: string;
  similarity_score?: number;
  processing_time?: number;
  image_urls?: {
    image1_url: string;
    image2_url: string;
  };
}

// 체인 실행 스테이지 타입
export interface ChainExecutionStage {
  chain_id: string;
  stage: number;
  stage_name: string;
  task_id: string | null;
  status: TaskStatus;
  progress: number;
  created_at: number;
  started_at: number;
  updated_at: number;
  error_message: string | null;
  description: string;
  expected_duration: string;
}

// 파이프라인 상태 응답 타입
export interface PipelineStatusResponse {
  chain_id: string;
  total_stages: number;
  current_stage: number | null;
  overall_progress: number;
  stages: ChainExecutionStage[];
}
