# React 기반 프론트엔드 프로젝트

이 프로젝트는 FastAPI 백엔드와 상호작용하기 위해 만들어진 모던 프론트엔드 애플리케이션입니다. React, TypeScript, Vite를 기반으로 구축되었으며, 기능 기반 아키텍처(Feature-Based Architecture)를 채택하여 유지보수성과 확장성을 높였습니다.

## ✨ 주요 특징

- **React & TypeScript**: 타입 안정성을 갖춘 컴포넌트 기반 UI 개발
- **Vite**: 매우 빠른 개발 서버 및 빌드 속도
- **Tailwind CSS**: 유틸리티 우선 CSS 프레임워크를 통한 신속한 스타일링
- **Feature-Based Architecture**: 도메인별로 코드를 구성하여 응집도 높고 결합도 낮은 구조
- **ESLint & Prettier**: 일관된 코드 스타일 및 품질 유지
- **Yarn Berry**: 모던하고 효율적인 의존성 관리

## 🛠️ 기술 스택

- **코어**: React, TypeScript
- **빌드 도구**: Vite
- **스타일링**: Tailwind CSS
- **상태 관리**: Zustand (전역), React Query (서버)
- **라우팅**: React Router
- **HTTP 클라이언트**: Axios
- **패키지 매니저**: Yarn

## 🚀 시작하기

### 1. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고, 백엔드 API 서버 주소를 설정합니다.

```bash
cp .env.example .env
```

`.env` 파일 내용 예시:

```
VITE_API_URL=http://localhost:8000
```

### 2. 의존성 설치

Yarn을 사용하여 프로젝트 의존성을 설치합니다.

```bash
yarn install
```

### 3. 개발 서버 실행

Vite 개발 서버를 시작합니다.

```bash
yarn dev
```

이제 `http://localhost:5173` (또는 터미널에 표시된 다른 포트)에서 애플리케이션을 확인할 수 있습니다.

## NPM 스크립트

- `yarn dev`: 개발 서버를 시작합니다.
- `yarn build`: 프로덕션용으로 앱을 빌드합니다.
- `yarn lint`: ESLint로 코드 품질을 검사합니다.
- `yarn preview`: 프로덕션 빌드 결과물을 미리 봅니다.

## 📁 프로젝트 구조

이 프로젝트는 기능 기반 아키텍처를 따릅니다.

```
src/
├── features/           # 도메인별 기능 모듈 (예: 챗봇, 사용자 인증)
│   └── [feature]/
├── shared/             # 여러 기능에서 공유되는 리소스
│   ├── components/     # 공통 UI 컴포넌트
│   ├── hooks/          # 공통 React Hooks
│   ├── stores/         # 전역 상태 관리 (Zustand)
│   ├── types/          # 공통 TypeScript 타입
│   └── utils/          # 유틸리티 함수
├── pages/              # 라우팅되는 페이지 컴포넌트
├── layouts/            # 페이지 레이아웃 컴포넌트
└── App.tsx             # 애플리케이션 최상위 루트 컴포넌트
```

git config user.name "ybkim" && git config user.email "dydqls5757@gmail.com"
