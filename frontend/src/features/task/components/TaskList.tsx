import React from 'react';
import { TaskStatusCard } from './TaskStatusCard';
import type { ActiveTask, TaskStatusResponse } from '../types';

interface TaskListProps {
  tasks: ActiveTask[];
  onCancel: (taskId: string) => void;
  cancelingTasks: Set<string>;
}

export const TaskList: React.FC<TaskListProps> = ({
  tasks,
  onCancel,
  cancelingTasks,
}) => {
  if (!tasks || tasks.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">활성 태스크가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {tasks.map((task) => {
        const taskStatus: TaskStatusResponse = {
          task_id: task.task_id,
          status: 'PENDING',
          message: `${task.name} 태스크`,
        };
        
        return (
          <TaskStatusCard
            key={task.task_id}
            taskStatus={taskStatus}
            onCancel={onCancel}
            isCanceling={cancelingTasks.has(task.task_id)}
          />
        );
      })}
    </div>
  );
};