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

// 태스크 상태 응답 타입
export interface TaskStatusResponse {
  task_id: string;
  step: number;
  task_name: string;
  status: TaskStatus;
  progress: number;
  result?: string;
  traceback?: string;
}
// 모델 관련 타입들
export interface ServerInfo {
  url: string;
  name: string;
}

export interface ModelsResponse {
  servers: Record<string, ServerInfo>;
  available_models: string[];
}

// 채팅 예측 API 관련 타입들
export interface ChatPredictRequest {
  prompt: string;
  model: string;
  stream: boolean;
}

export interface ChatPredictResponse {
  response: string;
  model: string;
  tokens_used?: number;
  processing_time?: number;
}

// pipeline 관련 타입 re-export
export type { PipelineStatusResponse, ChainExecutionResponseDto } from './pipeline';
