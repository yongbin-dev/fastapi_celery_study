# 개발 가이드라인

## 🎯 코딩 표준

### TypeScript 규칙

#### 타입 정의
```typescript
// ✅ Interface 사용 (객체 구조)
interface User {
  id: string;
  name: string;
  email: string;
}

// ✅ Type 사용 (유니온, 리터럴)
type Status = 'loading' | 'success' | 'error';
type Theme = 'light' | 'dark';

// ✅ Generic 활용
interface ApiResponse<T> {
  data: T;
  success: boolean;
}
```

#### Props 타입
```typescript
// ✅ Interface로 Props 정의
interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
}) => {
  // ...
};
```

#### Hooks 타입
```typescript
// ✅ 리턴 타입 명시
export const useApi = <T>(url: string): {
  data: T | null;
  loading: boolean;
  error: string | null;
} => {
  // ...
};

// ✅ Tuple 리턴 시 const assertion
export const useToggle = (initial = false) => {
  const [value, setValue] = useState(initial);
  const toggle = () => setValue(!value);
  
  return [value, toggle] as const;
};
```

### React 패턴

#### 컴포넌트 구조
```typescript
// ✅ 표준 컴포넌트 구조
import React, { useState, useEffect } from 'react';
import type { ComponentProps } from './types';

interface Props {
  // props 정의
}

export const Component: React.FC<Props> = ({ 
  prop1, 
  prop2 = 'default' 
}) => {
  // 1. State
  const [state, setState] = useState('');

  // 2. Effects
  useEffect(() => {
    // side effects
  }, []);

  // 3. Handlers
  const handleClick = () => {
    // event handlers
  };

  // 4. Render
  return (
    <div>
      {/* JSX */}
    </div>
  );
};
```

#### Custom Hooks 패턴
```typescript
// ✅ Custom Hook 구조
export const useFeature = (config?: FeatureConfig) => {
  // 1. State
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  // 2. Effects
  useEffect(() => {
    // initialization
  }, []);

  // 3. Methods
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // fetch logic
    } finally {
      setLoading(false);
    }
  }, []);

  // 4. Return
  return {
    data,
    loading,
    fetchData,
  };
};
```

## 📁 파일 명명 규칙

### 파일명
```
✅ 올바른 명명
- UserProfile.tsx       (컴포넌트)
- useUserAuth.ts        (훅)
- userApi.ts            (유틸리티)
- UserTypes.ts          (타입 파일)
- user-profile.css      (스타일)

❌ 잘못된 명명  
- userprofile.tsx
- use_user_auth.ts
- UserAPI.ts
- user_types.ts
```

### 변수명
```typescript
// ✅ camelCase
const userName = 'john';
const isAuthenticated = true;
const handleUserLogin = () => {};

// ✅ PascalCase (컴포넌트, 클래스, 인터페이스)
const UserProfile = () => {};
interface UserData {}
class UserService {}

// ✅ CONSTANT_CASE (상수)
const API_BASE_URL = 'https://api.example.com';
const MAX_RETRY_COUNT = 3;
```

## 🎨 스타일링 규칙

### Tailwind CSS 패턴

#### 클래스 순서
```typescript
// ✅ 논리적 순서: Layout → Spacing → Typography → Colors → Effects
<div className="
  flex flex-col          // Layout
  p-4 m-2               // Spacing  
  text-lg font-bold     // Typography
  text-blue-600         // Colors
  shadow-md rounded-lg  // Effects
">
```

#### 조건부 클래스
```typescript
// ✅ clsx 또는 유틸리티 함수 사용
import { cn } from '@/shared/utils';

<button className={cn(
  'px-4 py-2 rounded-md font-medium',
  variant === 'primary' && 'bg-blue-600 text-white',
  variant === 'secondary' && 'bg-gray-200 text-gray-800',
  disabled && 'opacity-50 cursor-not-allowed'
)}>
```

## 🪝 Hooks 사용 규칙

### useState
```typescript
// ✅ 명확한 초기값과 타입
const [user, setUser] = useState<User | null>(null);
const [isLoading, setIsLoading] = useState(false);

// ✅ 함수형 업데이트
setItems(prev => [...prev, newItem]);
```

### useEffect
```typescript
// ✅ 의존성 배열 명시
useEffect(() => {
  fetchData();
}, [userId]); // userId 변경시만 실행

// ✅ 클린업 함수
useEffect(() => {
  const subscription = api.subscribe();
  
  return () => {
    subscription.unsubscribe();
  };
}, []);
```

### useCallback & useMemo
```typescript
// ✅ 적절한 최적화
const expensiveCalculation = useMemo(() => {
  return heavyComputation(data);
}, [data]);

const handleClick = useCallback(() => {
  onItemClick(item.id);
}, [item.id, onItemClick]);
```

## 🔧 API & 데이터 관리

### API 호출
```typescript
// ✅ React Query 패턴
export const useUsers = () => {
  return useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers,
    staleTime: 5 * 60 * 1000, // 5분
  });
};

// ✅ Mutation 패턴
export const useCreateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};
```

### 에러 처리
```typescript
// ✅ 구체적인 에러 타입
interface ApiError {
  message: string;
  code: number;
  details?: Record<string, string[]>;
}

// ✅ Try-catch with 타입 가드
const handleApiCall = async () => {
  try {
    const result = await apiCall();
    return result;
  } catch (error) {
    if (error instanceof ApiError) {
      console.error('API Error:', error.message);
    } else {
      console.error('Unexpected error:', error);
    }
    throw error;
  }
};
```

## 🧪 테스트 패턴

### 컴포넌트 테스트
```typescript
// ✅ 기본 테스트 구조
describe('Button Component', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Hook 테스트
```typescript
// ✅ Hook 테스트
describe('useToggle', () => {
  it('toggles value correctly', () => {
    const { result } = renderHook(() => useToggle(false));
    
    expect(result.current[0]).toBe(false);
    
    act(() => {
      result.current[1](); // toggle
    });
    
    expect(result.current[0]).toBe(true);
  });
});
```

## 📦 의존성 관리

### Import 순서
```typescript
// 1. React & External libraries
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

// 2. Internal features
import { UserProfile } from '@/features/user';

// 3. Shared resources
import { Button } from '@/shared/components';

// 4. Types (별도 그룹)
import type { User } from '@/shared/types';

// 5. Relative imports
import { LocalComponent } from './LocalComponent';
```

### 의존성 원칙
```typescript
// ✅ 허용되는 의존성 방향
features/chatbot → shared/components  ✅
features/user → shared/hooks         ✅
shared/hooks → shared/utils          ✅

// ❌ 금지되는 의존성 방향
shared/components → features/chatbot  ❌
features/chatbot → features/user     ❌
```

## 🔒 보안 가이드라인

### 환경변수
```typescript
// ✅ 환경변수 사용
const API_URL = import.meta.env.VITE_API_URL;

// ❌ 하드코딩
const API_URL = 'https://api.myapp.com'; 
```

### XSS 방지
```typescript
// ✅ 안전한 HTML 렌더링
<div>{user.name}</div> // React가 자동 escape

// ❌ 위험한 HTML 렌더링
<div dangerouslySetInnerHTML={{ __html: userContent }} />
```

## 📋 코드 리뷰 체크리스트

### 기능
- [ ] 요구사항 충족
- [ ] 에러 처리 구현
- [ ] 로딩 상태 처리
- [ ] 접근성 고려

### 코드 품질
- [ ] TypeScript 타입 정의
- [ ] 적절한 변수/함수명
- [ ] 코드 중복 제거
- [ ] 적절한 추상화

### 성능
- [ ] 불필요한 리렌더링 방지
- [ ] 적절한 메모이제이션
- [ ] 번들 크기 고려
- [ ] 이미지 최적화

### 구조
- [ ] 올바른 폴더 위치
- [ ] 의존성 방향 준수
- [ ] Export/Import 패턴
- [ ] 재사용성 고려

---

💡 **참고**: 이 가이드라인은 팀의 컨벤션에 맞춰 수정할 수 있습니다.