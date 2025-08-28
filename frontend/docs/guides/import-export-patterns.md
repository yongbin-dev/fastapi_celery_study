# Import/Export 패턴 가이드

## 📦 Export 패턴

### Named Export (권장)

```typescript
// ✅ 권장 방식
export const Button = () => <button />;
export const Input = () => <input />;
export { Header } from './Header';
```

**장점:**
- Tree shaking에 유리
- 명시적인 import/export
- 리팩토링 시 안전

### Default Export

```typescript
// ⚠️ 페이지 컴포넌트만 사용
const DashboardPage = () => <div>Dashboard</div>;
export default DashboardPage;
```

**사용 시기:**
- 페이지 컴포넌트
- 단일 기능 모듈

## 🔄 Index 파일 패턴

### Barrel Exports

각 폴더의 `index.ts`를 통해 깔끔한 import 경로를 제공합니다.

```typescript
// src/features/chatbot/components/index.ts
export { ChatMessage } from './ChatMessage';
export { ChatInput } from './ChatInput';
export { TypingIndicator } from './TypingIndicator';
```

```typescript
// src/features/chatbot/index.ts
// Components
export * from './components';

// Hooks  
export * from './hooks';

// Pages
export * from './pages';

// Types
export * from './types';
```

## 📥 Import 패턴

### 절대 경로 Import (권장)

```typescript
// ✅ 절대 경로 사용
import { ChatBotPage } from '@/features/chatbot';
import { Button } from '@/shared/components';
import { useAuth } from '@/shared/hooks';
import type { User } from '@/shared/types';
```

### 상대 경로 Import

```typescript
// ⚠️ 같은 기능 내에서만 사용
import { ChatMessage } from '../components';
import type { Message } from '../types';
```

### Import 순서 규칙

```typescript
// 1. React 및 외부 라이브러리
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

// 2. 내부 절대 경로 (features)
import { UserProfile } from '@/features/user';

// 3. 내부 절대 경로 (shared)
import { Button } from '@/shared/components';
import { useApi } from '@/shared/hooks';

// 4. 타입 import (별도 그룹)
import type { User } from '@/shared/types';
import type { ComponentProps } from 'react';

// 5. 상대 경로 (같은 기능 내)
import { ChatMessage } from './ChatMessage';
import type { Message } from '../types';
```

## 🏗️ 구체적인 Export 구조

### Feature Export 예시

```typescript
// src/features/dashboard/components/index.ts
export { DashboardChart } from './DashboardChart';
export { DashboardCard } from './DashboardCard';
export { DashboardHeader } from './DashboardHeader';

// src/features/dashboard/hooks/index.ts
export { useDashboard } from './useDashboard';
export { useDashboardData } from './useDashboardData';

// src/features/dashboard/pages/index.ts
export { default as DashboardPage } from './DashboardPage';

// src/features/dashboard/types/index.ts
export interface DashboardData {
  id: string;
  value: number;
}

export interface DashboardConfig {
  refreshInterval: number;
}

// src/features/dashboard/index.ts
// 전체 기능 export
export * from './components';
export * from './hooks';  
export * from './pages';
export * from './types';
```

### Shared Export 예시

```typescript
// src/shared/components/index.ts
// UI Components
export { Button } from './ui/Button';
export { Input } from './ui/Input';

// Layout Components  
export { Header } from './common/Header';
export { Footer } from './common/Footer';

// src/shared/hooks/index.ts
// Common hooks
export * from './common';

// Domain hooks
export * from './auth';
export * from './user';

// src/shared/types/index.ts
export interface User {
  id: string;
  email: string;
  name: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

// src/shared/index.ts
// 전체 공유 리소스 export
export * from './components';
export * from './hooks';
export * from './types';
export * from './utils';
export * from './stores';
```

## 🎯 Import 사용 예시

### Feature 컴포넌트에서

```typescript
// src/features/dashboard/pages/DashboardPage.tsx
import React from 'react';

// Shared 리소스
import { Button, Header } from '@/shared/components';
import { useAuth } from '@/shared/hooks';
import type { User } from '@/shared/types';

// 같은 기능 내 리소스
import { DashboardChart } from '../components';
import { useDashboard } from '../hooks';
import type { DashboardData } from '../types';

const DashboardPage: React.FC = () => {
  // ...
};
```

### App.tsx에서

```typescript
// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Shared 컴포넌트
import { Header } from '@/shared/components';

// Feature 페이지들
import { ChatBotPage } from '@/features/chatbot';
import { DashboardPage } from '@/features/dashboard';

// 일반 페이지
import HomePage from '@/pages/HomePage';
```

## ⚡ TypeScript Import Types

### 타입만 import할 때

```typescript
// ✅ type keyword 사용
import type { User } from '@/shared/types';
import type { ComponentProps } from 'react';

// ✅ 혼합 import
import React, { type FC } from 'react';
import { Button, type ButtonProps } from '@/shared/components';
```

### Interface vs Type

```typescript
// ✅ Interface 사용 (확장 가능한 객체)
export interface User {
  id: string;
  name: string;
}

// ✅ Type 사용 (유니온, 복합 타입)
export type Status = 'loading' | 'success' | 'error';
export type ButtonVariant = 'primary' | 'secondary';
```

## 🚫 안티 패턴

### 피해야 할 Import

```typescript
// ❌ 깊은 경로 직접 참조
import { ChatMessage } from '@/features/chatbot/components/ChatMessage';

// ✅ Index를 통한 import
import { ChatMessage } from '@/features/chatbot';

// ❌ Default export에서 이름 변경
import DashBoard from '@/features/dashboard'; // 원본: DashboardPage

// ✅ Named export 사용
import { DashboardPage } from '@/features/dashboard';

// ❌ 전체 import
import * as Dashboard from '@/features/dashboard';

// ✅ 필요한 것만 import
import { DashboardPage, useDashboard } from '@/features/dashboard';
```

### 피해야 할 Export

```typescript
// ❌ Index에서 default export
export { default } from './DashboardPage';

// ✅ 명시적인 이름으로 export
export { default as DashboardPage } from './DashboardPage';

// ❌ 모든 것을 default export
export default {
  Button,
  Input,
  Header
};

// ✅ Named export 사용
export { Button, Input, Header };
```

## 📋 체크리스트

Export/Import 설정 시 확인사항:

- [ ] Named export 우선 사용
- [ ] 모든 폴더에 index.ts 파일 존재
- [ ] 절대 경로 import 사용
- [ ] Import 순서 규칙 준수
- [ ] 타입 import시 type keyword 사용
- [ ] 깊은 경로 직접 참조 금지
- [ ] Barrel export 활용

---

💡 **팁**: IDE의 auto-import 기능을 활용하되, import 경로가 올바른지 항상 확인하세요!