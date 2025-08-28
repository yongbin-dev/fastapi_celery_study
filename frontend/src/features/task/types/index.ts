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
export interface TaskResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface TaskStatusResponse {
  task_id: string;
  status: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  message: string;
  current?: number;
  total?: number;
  result?: any;
  error?: string;
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

// 태스크 히스토리 응답 타입들
export interface TaskHistoryResponse {
  tasks: HistoryTask[];
  statistics: {
    total_found: number;
    returned_count: number;
    time_range: string;
    by_status: Record<string, number>;
    by_task_type: Record<string, number>;
    current_active: {
      active_tasks: number;
      scheduled_tasks: number;
      reserved_tasks: number;
    };
    workers: string[];
  };
  filters_applied: {
    hours: number;
    status: string | null;
    task_name: string | null;
    limit: number;
  };
}

export interface HistoryTask {
  task_id: string;
  status: 'SUCCESS' | 'FAILURE' | 'PENDING' | 'PROGRESS' | 'REVOKED';
  task_name: string;
  date_done: string;
  result?: any;
  traceback?: string;
  task_time: string;
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
