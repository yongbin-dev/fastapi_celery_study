# 폴더 구조 가이드

## 📁 새로운 기능 추가하기

새로운 기능을 추가할 때 따라야 할 단계별 가이드입니다.

### 1. 기능 폴더 생성

```bash
mkdir -p src/features/[feature-name]/{components,hooks,pages,types}
```

예시:
```bash
mkdir -p src/features/dashboard/{components,hooks,pages,types}
```

### 2. 기본 파일 구조 생성

```
src/features/dashboard/
├── components/
│   └── index.ts
├── hooks/
│   └── index.ts
├── pages/
│   ├── DashboardPage.tsx
│   └── index.ts
├── types/
│   └── index.ts
└── index.ts
```

### 3. 기능별 파일 작성

#### 📄 Pages (필수)
```typescript
// src/features/dashboard/pages/DashboardPage.tsx
import React from 'react';

const DashboardPage: React.FC = () => {
  return (
    <div>
      <h1>Dashboard</h1>
    </div>
  );
};

export default DashboardPage;
```

#### 🧩 Components (선택)
```typescript
// src/features/dashboard/components/DashboardChart.tsx
import React from 'react';

interface DashboardChartProps {
  data: number[];
}

export const DashboardChart: React.FC<DashboardChartProps> = ({ data }) => {
  return <div>Chart Component</div>;
};
```

#### 🪝 Hooks (선택)
```typescript
// src/features/dashboard/hooks/useDashboard.ts
import { useState } from 'react';

export const useDashboard = () => {
  const [data, setData] = useState([]);
  
  return {
    data,
    setData,
  };
};
```

#### 📝 Types (선택)
```typescript
// src/features/dashboard/types/index.ts
export interface DashboardData {
  id: string;
  value: number;
  label: string;
}

export interface DashboardConfig {
  theme: 'light' | 'dark';
  autoRefresh: boolean;
}
```

### 4. Export 파일 작성

각 폴더의 `index.ts` 파일을 작성합니다:

```typescript
// src/features/dashboard/components/index.ts
export { DashboardChart } from './DashboardChart';

// src/features/dashboard/hooks/index.ts
export { useDashboard } from './useDashboard';

// src/features/dashboard/pages/index.ts
export { default as DashboardPage } from './DashboardPage';

// src/features/dashboard/types/index.ts
export * from './index';

// src/features/dashboard/index.ts
export * from './components';
export * from './hooks';
export * from './pages';
export * from './types';
```

### 5. 전역 Export 업데이트

```typescript
// src/features/index.ts
export * from './chatbot';
export * from './dashboard'; // 새로 추가
```

### 6. 라우팅 추가

```typescript
// src/App.tsx
import { DashboardPage } from '@/features/dashboard';

// Routes에 추가
<Route path="/dashboard" element={<DashboardPage />} />
```

## 🔄 공통 요소 추가하기

### Shared Components

```typescript
// src/shared/components/ui/Button.tsx
import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  onClick, 
  variant = 'primary' 
}) => {
  return (
    <button 
      onClick={onClick}
      className={`px-4 py-2 rounded ${
        variant === 'primary' ? 'bg-blue-600 text-white' : 'bg-gray-200'
      }`}
    >
      {children}
    </button>
  );
};
```

### Shared Hooks

```typescript
// src/shared/hooks/common/useToggle.ts
import { useState, useCallback } from 'react';

export const useToggle = (initialValue = false) => {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => {
    setValue(prev => !prev);
  }, []);

  return [value, toggle] as const;
};
```

### Shared Types

```typescript
// src/shared/types/api.ts
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  page: number;
  limit: number;
  total: number;
}
```

## 📂 파일 명명 규칙

### 컴포넌트
- **PascalCase**: `DashboardChart.tsx`
- **기능 + 역할**: `UserProfileCard.tsx`

### Hooks
- **camelCase**: `useDashboard.ts`
- **use 접두사**: `useUserAuth.ts`

### 페이지
- **PascalCase + Page**: `DashboardPage.tsx`

### 타입
- **PascalCase**: `User`, `DashboardData`
- **Interface 접두사** (선택): `IUser`, `IDashboardData`

### 폴더
- **kebab-case**: `user-profile`
- **단수형 사용**: `component` (not `components`)

## ❌ 피해야 할 패턴

### 🚫 잘못된 의존성
```typescript
// ❌ Feature 간 직접 참조
import { ChatMessage } from '@/features/chatbot/components';

// ✅ 공통 컴포넌트로 추상화
import { MessageBubble } from '@/shared/components';
```

### 🚫 잘못된 파일 위치
```typescript
// ❌ 특정 기능에만 사용되는 컴포넌트를 shared에
src/shared/components/ChatBubble.tsx

// ✅ 해당 기능 폴더에
src/features/chatbot/components/ChatBubble.tsx
```

### 🚫 순환 의존성
```typescript
// ❌ features/a에서 features/b 참조
import { FeatureB } from '@/features/b';

// ✅ 공통 로직은 shared로
import { CommonLogic } from '@/shared/utils';
```

## 📋 체크리스트

새로운 기능 추가 시 확인사항:

- [ ] 적절한 폴더 구조 생성
- [ ] 모든 index.ts 파일 작성
- [ ] 전역 export 업데이트
- [ ] 라우팅 설정
- [ ] 의존성 방향 확인
- [ ] TypeScript 타입 정의
- [ ] 공통 요소 재사용 확인

---

💡 **팁**: VS Code에서 폴더 템플릿을 만들어 두면 빠르게 기능을 추가할 수 있습니다!