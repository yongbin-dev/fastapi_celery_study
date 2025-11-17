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
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatPredictRequest {
  messages: ChatMessage[];
  model?: string;
  description?: string;
}

// OpenAI 호환 응답 형식
export interface ChatCompletionMessage {
  content: string;
  role: string;
  refusal: string | null;
  annotations: unknown | null;
  audio: unknown | null;
  function_call: unknown | null;
  tool_calls: unknown[];
  reasoning_content: string | null;
}

export interface ChatCompletionChoice {
  finish_reason: string;
  index: number;
  logprobs: unknown | null;
  message: ChatCompletionMessage;
  stop_reason: string | null;
  token_ids: unknown | null;
}

export interface ChatCompletionUsage {
  completion_tokens: number;
  prompt_tokens: number;
  total_tokens: number;
  completion_tokens_details: unknown | null;
  prompt_tokens_details: unknown | null;
}

export interface ChatCompletionResult {
  id: string;
  choices: ChatCompletionChoice[];
  created: number;
  model: string;
  object: string;
  service_tier: string | null;
  system_fingerprint: string | null;
  usage: ChatCompletionUsage;
  prompt_logprobs: unknown | null;
  prompt_token_ids: unknown | null;
  kv_transfer_params: unknown | null;
}

export interface ChatPredictResponse {
  data: {
    servers: string;
    result: ChatCompletionResult;
  };
  message: string;
}

// pipeline 관련 타입 re-export
export type { PipelineStatusResponse, ChainExecutionResponseDto } from './pipeline';
