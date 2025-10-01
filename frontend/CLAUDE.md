# CLAUDE.md

이 파일은 React Feature-Based Architecture 프로젝트에서 Claude Code가 일관된 방식으로 개발할 수 있도록 가이드를 제공합니다.

## 🌍 언어 설정

- **주 언어**: 한국어
- **커뮤니케이션**: 모든 응답과 설명은 한국어로 작성
- **코드 주석**: 한국어로 작성 (필요시에만)
- **변수/함수명**: 영어 사용 (기술적 표준 준수)

## 🏗️ 프로젝트 아키텍처

### Feature-Based Architecture 사용

```
src/
├── features/           # 도메인별 기능 모듈
│   ├── chatbot/       # 예시: 챗봇 기능
│   └── [feature]/     # 각 기능은 독립적인 폴더
├── shared/            # 공유 리소스
│   ├── components/    # 공통 컴포넌트
│   ├── hooks/        # 공통 hooks
│   ├── types/        # 공통 타입
│   ├── utils/        # 유틸리티
│   └── stores/       # 전역 상태
├── pages/            # 일반 페이지
└── App.tsx          # 애플리케이션 루트
```

자세한 내용: [docs/architecture/README.md](./docs/architecture/README.md)

## 🛠️ 개발 명령어

### 핵심 개발

- `npm run dev` - 개발 서버 시작
- `npm run build` - 프로덕션 빌드
- `npm run lint` - 코드 품질 검사
- `npm run preview` - 빌드 결과 미리보기

### 코드 품질

- ESLint + Prettier 설정 완료
- TypeScript strict 모드 사용
- Tailwind CSS로 스타일링

## 📁 새로운 기능 추가 가이드

### 1. 폴더 생성

```bash
mkdir -p src/features/[feature-name]/{components,hooks,pages,types}
```

### 2. 필수 파일 생성

각 폴더마다 `index.ts` 파일 생성 후 적절한 export 설정

### 3. 기능별 구조

- **components/**: 해당 기능 전용 컴포넌트
- **hooks/**: 해당 기능 전용 비즈니스 로직
- **pages/**: 해당 기능의 페이지들
- **types/**: 해당 기능 타입 정의

### 4. Export 패턴

```typescript
// src/features/[feature-name]/index.ts
export * from './components';
export * from './hooks';
export * from './pages';
export * from './types';
```

자세한 내용: [docs/guides/folder-structure.md](./docs/guides/folder-structure.md)

## 📦 Import/Export 규칙

### Import 우선순위

```typescript
// 1. React & 외부 라이브러리
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

// 2. Features
import { UserProfile } from '@/features/user';

// 3. Shared 리소스
import { Button } from '@/shared/components';
import { useAuth } from '@/shared/hooks';

// 4. 타입 (별도 그룹)
import type { User } from '@/shared/types';

// 5. 상대 경로 (같은 기능 내)
import { LocalComponent } from './LocalComponent';
```

### Export 패턴

- **Named Export 우선 사용** (Tree shaking 최적화)
- **Default Export**는 페이지 컴포넌트만
- **Barrel Exports** (index.ts) 활용

자세한 내용: [docs/guides/import-export-patterns.md](./docs/guides/import-export-patterns.md)

## 🎯 코딩 표준

### TypeScript 규칙

```typescript
// ✅ Interface 사용 (객체 구조)
interface User {
  id: string;
  name: string;
}

// ✅ Type 사용 (유니온, 리터럴)
type Status = 'loading' | 'success' | 'error';

// ✅ Props 명시적 타입 정의
interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
}
```

### React 패턴

```typescript
// ✅ 표준 컴포넌트 구조
export const Component: React.FC<Props> = ({ prop1, prop2 }) => {
  // 1. State
  const [state, setState] = useState('');

  // 2. Effects
  useEffect(() => {
    // side effects
  }, []);

  // 3. Handlers
  const handleClick = () => {};

  // 4. Render
  return <div>{/* JSX */}</div>;
};
```

### 네이밍 규칙

- **컴포넌트**: PascalCase (`UserProfile.tsx`)
- **Hooks**: camelCase + use 접두사 (`useUserAuth.ts`)
- **페이지**: PascalCase + Page (`UserPage.tsx`)
- **변수**: camelCase (`userName`)
- **상수**: CONSTANT_CASE (`API_BASE_URL`)

자세한 내용: [docs/guides/development-guidelines.md](./docs/guides/development-guidelines.md)

## 🔄 의존성 관리 규칙

### ✅ 허용되는 의존성 방향

- `features/[feature]` → `shared/*` ✅
- `shared/hooks` → `shared/utils` ✅

### ❌ 금지되는 의존성 방향

- `shared/*` → `features/*` ❌
- `features/[feature-a]` → `features/[feature-b]` ❌

### 공통 요소 처리

기능 간 공유가 필요한 경우 `shared/` 폴더로 추상화

## 🧪 개발 시 체크리스트

### 새 기능 개발 시

- [ ] 적절한 폴더 구조 생성
- [ ] TypeScript 타입 정의
- [ ] 모든 index.ts 파일 작성
- [ ] 의존성 방향 준수
- [ ] Named Export 사용
- [ ] 에러 처리 구현
- [ ] 로딩 상태 처리

### 코드 리뷰 시

- [ ] 폴더 구조 확인
- [ ] Import/Export 패턴 준수
- [ ] 코딩 표준 준수
- [ ] 재사용성 고려
- [ ] 성능 최적화

## 📚 참고 문서

- [📋 아키텍처 개요](./docs/architecture/README.md)
- [📁 폴더 구조 가이드](./docs/guides/folder-structure.md)
- [📦 Import/Export 패턴](./docs/guides/import-export-patterns.md)
- [🎯 개발 가이드라인](./docs/guides/development-guidelines.md)
- [💡 구현 예시](./docs/examples/feature-example.md)

## 🚀 기술 스택

### Core

- **React 19** + **TypeScript**
- **Vite** (빌드 도구)
- **Tailwind CSS** (스타일링)

### 상태 관리

- **Zustand** (전역 상태)
- **React Query** (서버 상태)

### 개발 도구

- **ESLint** + **Prettier**
- **React Router** (라우팅)
- **Axios** (HTTP 클라이언트)

---
