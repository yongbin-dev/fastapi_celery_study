// 태스크 요청 타입들
export interface TaskRequest {
  message: string;
  delay?: number;
}

export interface TaskHistoryRequest {
  hours: number;
  status: string;
  task_name: string;
  limit: number;
}

export interface AITaskRequest {
  text: string;
  max_length?: number;
}

export interface EmailTaskRequest {
  to_email: string;
  subject: string;
  body: string;
}

export interface LongTaskRequest {
  total_steps?: number;
  step_delay?: number;
}

// API 공통 응답 래퍼
export interface ApiResponse<T> {
  success: boolean;
  status: string;
  message: string;
  timestamp: string;
  data: T;
}

// 태스크 응답 타입들
export interface TaskInfoResponse {
  task_id: string;
  status: string;
  task_name: string;
  args: string;
  kwargs: string;
  result: string;
  error_message: string;
  traceback: string;
  retry_count: number;
  task_time: string;
  completed_time: string;

  // Chain 관련
  root_task_id: string;
  parent_task_id?: string;
  chain_id?: string;
  chain_position?: number;
  chain_total?: number;
}

export interface ActiveTasksResponse {
  active_tasks: ActiveTask[];
  total_count: number;
}

export interface ActiveTask {
  task_id: string;
  name: string;
  worker: string;
  args: any[];
  kwargs: Record<string, any>;
}

// 파이프라인 태스크 정보
export interface PipelineTask {
  task_id: string;
  status: string;
  task_name: string;
  result: string;
  traceback: string | null;
  step: number;
  ready: boolean;
  progress: number;
}

// 파이프라인 히스토리 정보
export interface PipelineHistoryInfo {
  pipeline_id: string;
  overall_state: string;
  total_steps: number;
  current_stage: number;
  start_time: string;
  tasks: PipelineTask[];
}

// 태스크 히스토리 응답 타입들
export interface TaskHistoryResponse {
  data: PipelineHistoryInfo[];
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
  status: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
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

// 기존 호환성을 위한 레거시 타입들 (필요시 제거 예정)
export interface TaskStatusResponse {
  task_id: string;
  status: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  task_name: string;
  result: string;
  traceback: string;
  step: number;
  ready: boolean;
  progress: number;
}

export interface LegacyPipelineStatusResponse {
  pipeline_id: string;
  overall_state: string;
  total_steps: number;
  current_stage: number;
  start_time: string;
  tasks: TaskStatusResponse[];
}
