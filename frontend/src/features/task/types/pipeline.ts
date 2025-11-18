import { TaskStatus } from ".";
export type PROCESS_STATE = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILURE' | 'CANCELLED';

export interface TaskLog {
  id: number;
  task_id: string;
  task_name: string;
  status: string;
  chain_execution_id: number;
  started_at: string;
  finished_at: string | null;
}

export interface ChainExecutionResponseDto {
  id: number;
  status: string;
  batch_id: string;
  started_at: string;
  finished_at: string | null;
  initiated_by: string;
  input_data: Record<string, any>;
  final_result: any | null;
  error_message: string | null;
  task_logs: TaskLog[];
}

// 파이프라인 상태 응답 (간단한 버전)
export interface PipelineStatusResponse {
  task_id: string;
  status: TaskStatus;
  message: string;
  result : string;
}

// OCR TextBox 정보
export interface OcrTextBox {
  ocrExecutionId: string | null;
  text: string;
  confidence: number;
  bbox: number[][];
}

// OCR 결과 정보
export interface OcrResult {
  error: string | null;
  textBoxes: OcrTextBox[];
}

// Batch 내 Context 정보
export interface BatchContext {
  batch_id: string;
  chain_execution_id: string;
  private_img: string;
  public_file_path: string;
  private_imgs: string[];
  public_file_paths: string[];
  is_batch: boolean;
  options: Record<string, any>;
  ocr_result: OcrResult | null;
  ocr_results: OcrResult[];
  llm_result: any | null;
  status: string;
  current_stage: string;
  error: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
}

// Batch 상태 응답
export interface BatchStatusResponse {
  batch_id: string;
  total_count: number;
  contexts: BatchContext[];
}

// 파이프라인 리스트 관련 타입
export interface Task {
  id: string;
  name: string;
  status: PROCESS_STATE;
  progress?: number;
  createdAt?: string;
}

export interface Batch {
  id: string;
  name: string;
  status: PROCESS_STATE;
  tasks: Task[];
  createdAt?: string;
}

export interface Pipeline {
  id: string;
  name: string;
  status: PROCESS_STATE;
  batches: Batch[];
  createdAt?: string;
}
