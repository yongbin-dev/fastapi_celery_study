# React 프로젝트 아키텍처

## 📋 목차
- [개요](#개요)
- [아키텍처 패턴](#아키텍처-패턴)
- [폴더 구조](#폴더-구조)
- [설계 원칙](#설계-원칙)
- [기술 스택](#기술-스택)

## 개요

이 프로젝트는 **Feature-Based Architecture** (기능 중심 아키텍처)를 채택하여 확장성과 유지보수성을 극대화했습니다. 각 기능(Feature)은 독립적인 모듈로 구성되어 있으며, 공통 요소는 `shared` 폴더에서 관리됩니다.

## 아키텍처 패턴

### Feature-Based Architecture

```
src/
├── features/     # 도메인별 기능 모듈
├── shared/       # 공유 리소스
├── pages/        # 일반 페이지
└── App.tsx       # 애플리케이션 진입점
```

**장점:**
- ✅ 기능별 코드 격리
- ✅ 확장성과 유지보수성
- ✅ 팀 단위 개발 용이
- ✅ 테스트 격리 가능
- ✅ 의존성 관리 명확

## 폴더 구조

### 전체 구조
```
src/
├── features/              # 🎯 도메인별 기능
│   ├── chatbot/          # 챗봇 기능
│   │   ├── components/   # 전용 컴포넌트
│   │   ├── hooks/        # 전용 hooks
│   │   ├── pages/        # 기능 페이지
│   │   ├── types/        # 타입 정의
│   │   └── index.ts      # 기능 진입점
│   └── index.ts          # 전체 기능 export
├── shared/               # 🔄 공유 리소스
│   ├── components/       # 공통 컴포넌트
│   ├── hooks/           # 공통 hooks
│   ├── types/           # 공통 타입
│   ├── utils/           # 유틸리티
│   ├── stores/          # 상태 관리
│   └── index.ts         # 공유 리소스 export
├── pages/               # 📄 일반 페이지
└── App.tsx              # 🏠 애플리케이션 루트
```

### Features 구조 상세

각 Feature는 다음과 같은 표준 구조를 가집니다:

```
features/[feature-name]/
├── components/          # 해당 기능 전용 컴포넌트
│   ├── ComponentA.tsx
│   ├── ComponentB.tsx
│   └── index.ts        # 컴포넌트 export
├── hooks/              # 해당 기능 전용 hooks
│   ├── useFeature.ts
│   └── index.ts        # hooks export
├── pages/              # 해당 기능의 페이지들
│   ├── FeaturePage.tsx
│   └── index.ts        # 페이지 export
├── types/              # 해당 기능 타입 정의
│   └── index.ts        # 타입 export
└── index.ts            # 전체 기능 export
```

### Shared 구조 상세

```
shared/
├── components/         # 재사용 가능한 공통 컴포넌트
│   ├── common/        # 기본 UI 컴포넌트
│   ├── ui/            # 디자인 시스템 컴포넌트
│   ├── forms/         # 폼 관련 컴포넌트
│   └── index.ts       # 컴포넌트 export
├── hooks/             # 공통 custom hooks
│   ├── common/        # 기본 유틸리티 hooks
│   ├── auth/          # 인증 관련 hooks
│   ├── user/          # 사용자 관리 hooks
│   └── index.ts       # hooks export
├── types/             # 전역 타입 정의
│   └── index.ts       # 타입 export
├── utils/             # 유틸리티 함수
│   ├── api.ts         # API 관련 유틸
│   └── index.ts       # 유틸 export
├── stores/            # 전역 상태 관리
│   ├── useAuthStore.ts
│   └── index.ts       # store export
└── index.ts           # 전체 공유 리소스 export
```

## 설계 원칙

### 1. 단일 책임 원칙 (SRP)
각 Feature는 하나의 비즈니스 도메인만 담당합니다.

### 2. 의존성 역전 원칙 (DIP)
- Features는 Shared 리소스에 의존할 수 있음
- Shared 리소스는 Features에 의존하면 안됨
- Features 간 직접 의존 금지

### 3. 개방-폐쇄 원칙 (OCP)
새로운 기능 추가 시 기존 코드 수정 없이 확장 가능해야 합니다.

### 4. 관심사 분리 (SoC)
각 폴더와 파일은 명확한 역할을 가져야 합니다.

## 기술 스택

### Core
- **React 19** - UI 라이브러리
- **TypeScript** - 타입 안정성
- **Vite** - 빌드 도구

### 상태 관리
- **Zustand** - 경량 상태 관리
- **React Query** - 서버 상태 관리

### 스타일링
- **Tailwind CSS** - 유틸리티 CSS

### 개발 도구
- **ESLint** - 코드 품질
- **Prettier** - 코드 포맷팅

### 네트워킹
- **Axios** - HTTP 클라이언트

---

📚 더 자세한 내용은 [가이드 문서](../guides/)를 참고하세요.