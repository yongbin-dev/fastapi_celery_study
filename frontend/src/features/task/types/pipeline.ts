export interface Task {
  id: number;
  task_id: string;
  task_name: string;
  status: string;
  args: string;
  kwargs: string | null;
  result: string;
  error: string | null;
  started_at: string | null;
  completed_at: string;
  retries: number;
  chain_execution_id: number;
  created_at: string;
  updated_at: string;
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
  task_logs: Task[];
}
