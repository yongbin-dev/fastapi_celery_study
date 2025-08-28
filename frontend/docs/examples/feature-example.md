# 기능 구현 예시

이 문서는 새로운 기능을 구현할 때 참고할 수 있는 실제 예시를 제공합니다.

## 📋 예시: Todo 기능 구현

### 1. 폴더 구조 생성

```bash
mkdir -p src/features/todo/{components,hooks,pages,types}
```

### 2. 타입 정의

```typescript
// src/features/todo/types/index.ts
export interface Todo {
  id: string;
  title: string;
  completed: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface CreateTodoData {
  title: string;
}

export interface UpdateTodoData {
  title?: string;
  completed?: boolean;
}

export interface TodoFilters {
  status: 'all' | 'active' | 'completed';
  search: string;
}
```

### 3. API Hooks

```typescript
// src/features/todo/hooks/useTodoApi.ts
import { useGet, usePost, usePut, useDelete } from '@/shared/hooks/common';
import type { Todo, CreateTodoData, UpdateTodoData } from '../types';

// 할일 목록 조회
export const useTodos = (filters?: Partial<TodoFilters>) => {
  const queryString = new URLSearchParams(filters as Record<string, string>).toString();
  
  return useGet<Todo[]>(
    ['todos', filters], 
    `/todos?${queryString}`,
    {
      staleTime: 30 * 1000, // 30초
    }
  );
};

// 할일 생성
export const useCreateTodo = () => {
  return usePost<Todo, CreateTodoData>('/todos', {
    onSuccess: (data) => {
      console.log('할일이 생성되었습니다:', data.title);
    },
  });
};

// 할일 수정
export const useUpdateTodo = (todoId: string) => {
  return usePut<Todo, UpdateTodoData>(`/todos/${todoId}`, {
    onSuccess: (data) => {
      console.log('할일이 수정되었습니다:', data.title);
    },
  });
};

// 할일 삭제
export const useDeleteTodo = () => {
  return useDelete<{ message: string }>('/todos', {
    onSuccess: () => {
      console.log('할일이 삭제되었습니다');
    },
  });
};
```

### 4. 비즈니스 로직 Hook

```typescript
// src/features/todo/hooks/useTodo.ts
import { useState, useMemo } from 'react';
import { useTodos, useCreateTodo, useUpdateTodo, useDeleteTodo } from './useTodoApi';
import type { Todo, TodoFilters } from '../types';

export const useTodo = () => {
  const [filters, setFilters] = useState<TodoFilters>({
    status: 'all',
    search: '',
  });

  // API calls
  const { data: todos = [], isLoading, error } = useTodos(filters);
  const createTodo = useCreateTodo();
  const updateTodo = useUpdateTodo('');
  const deleteTodo = useDeleteTodo();

  // Computed values
  const filteredTodos = useMemo(() => {
    return todos.filter(todo => {
      // Status filter
      if (filters.status === 'active' && todo.completed) return false;
      if (filters.status === 'completed' && !todo.completed) return false;
      
      // Search filter
      if (filters.search && !todo.title.toLowerCase().includes(filters.search.toLowerCase())) {
        return false;
      }
      
      return true;
    });
  }, [todos, filters]);

  const stats = useMemo(() => {
    const total = todos.length;
    const completed = todos.filter(todo => todo.completed).length;
    const active = total - completed;
    
    return { total, completed, active };
  }, [todos]);

  // Actions
  const handleCreateTodo = async (title: string) => {
    try {
      await createTodo.mutateAsync({ title });
    } catch (error) {
      console.error('할일 생성 실패:', error);
    }
  };

  const handleToggleTodo = async (todo: Todo) => {
    try {
      // updateTodo hook을 새로 생성해야 하므로 실제로는 다른 방식 사용
      await updateTodo.mutateAsync({ completed: !todo.completed });
    } catch (error) {
      console.error('할일 토글 실패:', error);
    }
  };

  const handleDeleteTodo = async (todoId: string) => {
    try {
      await deleteTodo.mutateAsync();
    } catch (error) {
      console.error('할일 삭제 실패:', error);
    }
  };

  return {
    // Data
    todos: filteredTodos,
    stats,
    isLoading,
    error,

    // Filters
    filters,
    setFilters,

    // Actions
    createTodo: handleCreateTodo,
    toggleTodo: handleToggleTodo,
    deleteTodo: handleDeleteTodo,

    // Loading states
    isCreating: createTodo.isPending,
    isUpdating: updateTodo.isPending,
    isDeleting: deleteTodo.isPending,
  };
};
```

### 5. UI Components

```typescript
// src/features/todo/components/TodoItem.tsx
import React from 'react';
import { Button } from '@/shared/components';
import type { Todo } from '../types';

interface TodoItemProps {
  todo: Todo;
  onToggle: (todo: Todo) => void;
  onDelete: (todoId: string) => void;
}

export const TodoItem: React.FC<TodoItemProps> = ({ 
  todo, 
  onToggle, 
  onDelete 
}) => {
  return (
    <div className="flex items-center gap-3 p-3 border rounded-lg">
      <input
        type="checkbox"
        checked={todo.completed}
        onChange={() => onToggle(todo)}
        className="w-4 h-4"
      />
      
      <span className={`flex-1 ${todo.completed ? 'line-through text-gray-500' : ''}`}>
        {todo.title}
      </span>
      
      <Button
        onClick={() => onDelete(todo.id)}
        variant="secondary"
        size="sm"
      >
        삭제
      </Button>
    </div>
  );
};
```

```typescript
// src/features/todo/components/TodoForm.tsx
import React, { useState } from 'react';
import { Button } from '@/shared/components';

interface TodoFormProps {
  onSubmit: (title: string) => void;
  isLoading?: boolean;
}

export const TodoForm: React.FC<TodoFormProps> = ({ 
  onSubmit, 
  isLoading = false 
}) => {
  const [title, setTitle] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (title.trim()) {
      onSubmit(title.trim());
      setTitle('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 mb-6">
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="할일을 입력하세요..."
        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <Button
        type="submit"
        disabled={!title.trim() || isLoading}
      >
        {isLoading ? '추가 중...' : '추가'}
      </Button>
    </form>
  );
};
```

```typescript
// src/features/todo/components/TodoFilters.tsx
import React from 'react';
import type { TodoFilters } from '../types';

interface TodoFiltersProps {
  filters: TodoFilters;
  onFiltersChange: (filters: TodoFilters) => void;
  stats: {
    total: number;
    active: number;
    completed: number;
  };
}

export const TodoFilters: React.FC<TodoFiltersProps> = ({
  filters,
  onFiltersChange,
  stats,
}) => {
  const statusOptions = [
    { value: 'all' as const, label: `전체 (${stats.total})` },
    { value: 'active' as const, label: `진행중 (${stats.active})` },
    { value: 'completed' as const, label: `완료 (${stats.completed})` },
  ];

  return (
    <div className="flex flex-col gap-4 mb-6">
      {/* Status Filter */}
      <div className="flex gap-2">
        {statusOptions.map(option => (
          <button
            key={option.value}
            onClick={() => onFiltersChange({ ...filters, status: option.value })}
            className={`px-3 py-1 rounded-md text-sm ${
              filters.status === option.value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {/* Search Filter */}
      <input
        type="text"
        value={filters.search}
        onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
        placeholder="할일 검색..."
        className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
  );
};
```

### 6. 페이지 컴포넌트

```typescript
// src/features/todo/pages/TodoPage.tsx
import React from 'react';
import { TodoForm, TodoItem, TodoFilters } from '../components';
import { useTodo } from '../hooks/useTodo';

const TodoPage: React.FC = () => {
  const {
    todos,
    stats,
    isLoading,
    error,
    filters,
    setFilters,
    createTodo,
    toggleTodo,
    deleteTodo,
    isCreating,
  } = useTodo();

  if (error) {
    return (
      <div className="p-8">
        <div className="text-red-600">
          할일을 불러오는데 실패했습니다: {error.message}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-3xl font-bold text-center mb-8">할일 관리</h1>

      <TodoForm 
        onSubmit={createTodo} 
        isLoading={isCreating} 
      />

      <TodoFilters
        filters={filters}
        onFiltersChange={setFilters}
        stats={stats}
      />

      {isLoading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        </div>
      ) : (
        <div className="space-y-2">
          {todos.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {filters.status === 'all' ? '할일이 없습니다' : `${filters.status} 할일이 없습니다`}
            </div>
          ) : (
            todos.map(todo => (
              <TodoItem
                key={todo.id}
                todo={todo}
                onToggle={toggleTodo}
                onDelete={deleteTodo}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default TodoPage;
```

### 7. Export 설정

```typescript
// src/features/todo/components/index.ts
export { TodoItem } from './TodoItem';
export { TodoForm } from './TodoForm';
export { TodoFilters } from './TodoFilters';

// src/features/todo/hooks/index.ts
export { useTodo } from './useTodo';
export * from './useTodoApi';

// src/features/todo/pages/index.ts
export { default as TodoPage } from './TodoPage';

// src/features/todo/index.ts
export * from './components';
export * from './hooks';
export * from './pages';
export * from './types';

// src/features/index.ts에 추가
export * from './todo';
```

### 8. 라우팅 설정

```typescript
// src/App.tsx에 추가
import { TodoPage } from '@/features/todo';

// Routes에 추가
<Route path="/todo" element={<TodoPage />} />
```

### 9. 네비게이션 업데이트

```typescript
// src/shared/components/common/Header.tsx에 추가
<Link
  to="/todo"
  className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
    isActive('/todo') 
      ? 'text-blue-600 bg-blue-50' 
      : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
  }`}
>
  Todo
</Link>
```

## 🎯 핵심 포인트

이 예시에서 보여준 패턴들:

1. **명확한 타입 정의**: 모든 데이터 구조를 타입으로 정의
2. **계층적 Hook 구조**: API Hook → 비즈니스 로직 Hook
3. **단일 책임 컴포넌트**: 각 컴포넌트는 하나의 역할만 담당
4. **Props 명시**: 모든 Props를 명확히 정의
5. **에러 처리**: API 호출과 렌더링에서 에러 처리
6. **로딩 상태**: 사용자에게 적절한 피드백 제공
7. **재사용성**: 다른 기능에서도 활용 가능한 구조

---

💡 **참고**: 이 예시를 참고하여 다른 기능들도 일관된 패턴으로 구현하세요!