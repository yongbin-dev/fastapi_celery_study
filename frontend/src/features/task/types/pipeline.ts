import { TaskStatus } from ".";

export interface TaskLog {
  id: number;
  task_id: string;
  task_name: string;
  status: string;
  chain_execution_id: number;
  started_at: string;
  finished_at: string;
}

export interface InputData {
  text: string;
  options: {
    model: string;
  };
  priority: number;
  callback_url: string | null;
}

export interface ChainExecutionResponseDto {
  id: number;
  chain_id: string;
  chain_name: string;
  status: string;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  created_at: string;
  started_at: string;
  finished_at: string;
  initiated_by: string;
  input_data: InputData;
  final_result: string | null;
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

// 파이프라인 리스트 관련 타입
export interface Task {
  id: string;
  name: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILURE' | 'CANCELLED';
  progress?: number;
  createdAt?: string;
}

export interface Batch {
  id: string;
  name: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILURE' | 'CANCELLED';
  tasks: Task[];
  createdAt?: string;
}

export interface Pipeline {
  id: string;
  name: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILURE' | 'CANCELLED';
  batches: Batch[];
  createdAt?: string;
}
