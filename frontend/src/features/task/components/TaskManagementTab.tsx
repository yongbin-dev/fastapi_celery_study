import React from 'react';
import { TaskForm, TaskList } from './';
import { 
  useCreateExampleTask,
  useCreateAITask,
  useCreateEmailTask,
  useCreateLongTask,
  useActiveTasks,
} from '../hooks';
import type { 
  TaskRequest, 
  AITaskRequest, 
  EmailTaskRequest, 
  LongTaskRequest
} from '../types';

interface TaskManagementTabProps {
  onCancelTask: (taskId: string) => Promise<void>;
  cancelingTasks: Set<string>;
}

export const TaskManagementTab: React.FC<TaskManagementTabProps> = ({
  onCancelTask,
  cancelingTasks,
}) => {
  const { data: activeTasksData, isLoading: isLoadingTasks } = useActiveTasks();
  const activeTasks = activeTasksData?.active_tasks || [];
  const createExampleTask = useCreateExampleTask();
  const createAITask = useCreateAITask();
  const createEmailTask = useCreateEmailTask();
  const createLongTask = useCreateLongTask();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* 태스크 생성 폼들 */}
      <div className="space-y-6">
        <TaskForm
          title="예제 태스크"
          onSubmit={(data: TaskRequest) => createExampleTask.mutate(data)}
          isLoading={createExampleTask.isPending}
          fields={[
            {
              name: 'message',
              label: '메시지',
              type: 'text',
              placeholder: '태스크 메시지를 입력하세요',
              required: true,
            },
            {
              name: 'delay',
              label: '지연 시간 (초)',
              type: 'number',
              defaultValue: 5,
              placeholder: '지연 시간을 입력하세요',
            },
          ]}
        />

        <TaskForm
          title="AI 태스크"
          onSubmit={(data: AITaskRequest) => createAITask.mutate(data)}
          isLoading={createAITask.isPending}
          fields={[
            {
              name: 'text',
              label: 'AI 텍스트',
              type: 'text',
              placeholder: 'AI에게 요청할 텍스트를 입력하세요',
              required: true,
            },
            {
              name: 'max_length',
              label: '최대 길이',
              type: 'number',
              defaultValue: 100,
              placeholder: '최대 길이를 입력하세요',
            },
          ]}
        />

        <TaskForm
          title="이메일 태스크"
          onSubmit={(data: EmailTaskRequest) => createEmailTask.mutate(data)}
          isLoading={createEmailTask.isPending}
          fields={[
            {
              name: 'to_email',
              label: '받는 사람',
              type: 'email',
              placeholder: '받는 사람 이메일을 입력하세요',
              required: true,
            },
            {
              name: 'subject',
              label: '제목',
              type: 'text',
              placeholder: '이메일 제목을 입력하세요',
              required: true,
            },
            {
              name: 'body',
              label: '내용',
              type: 'text',
              placeholder: '이메일 내용을 입력하세요',
              required: true,
            },
          ]}
        />

        <TaskForm
          title="긴 태스크"
          onSubmit={(data: LongTaskRequest) => createLongTask.mutate(data)}
          isLoading={createLongTask.isPending}
          fields={[
            {
              name: 'total_steps',
              label: '총 단계 수',
              type: 'number',
              defaultValue: 10,
              placeholder: '총 단계 수를 입력하세요',
              required: true,
            },
            {
              name: 'step_delay',
              label: '단계별 지연 시간 (초)',
              type: 'number',
              defaultValue: 2,
              placeholder: '각 단계별 지연 시간을 입력하세요',
            },
          ]}
        />
      </div>

      {/* 활성 태스크 목록 */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">활성 태스크 목록</h2>
          {isLoadingTasks && (
            <div className="text-sm text-gray-500">로딩 중...</div>
          )}
        </div>
        
        <TaskList
          tasks={activeTasks}
          onCancel={onCancelTask}
          cancelingTasks={cancelingTasks}
        />
      </div>
    </div>
  );
};