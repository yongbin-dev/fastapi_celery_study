# FastAPI, Celery, React 기반 풀스택 프로젝트

이 저장소는 FastAPI와 Celery를 사용하는 Python 백엔드와 React, TypeScript로 구축된 모던 프론트엔드를 통합한 풀스택 웹 애플리케이션 스터디 프로젝트입니다.

## 📂 프로젝트 구조

이 프로젝트는 두 개의 주요 디렉토리로 구성되어 있습니다:

- **`./backend/`**: FastAPI로 구축된 백엔드 서버입니다. API 로직, 데이터베이스 상호작용, Celery를 통한 비동기 백그라운드 작업을 처리합니다.
- **`./frontend/`**: React로 구축된 클라이언트 사이드 애플리케이션입니다. 백엔드 서버와 통신하여 사용자 인터페이스를 제공합니다.

각 디렉토리는 자체적인 의존성과 상세한 문서를 가진 독립적인 프로젝트입니다.

## 🚀 시작하기

전체 애플리케이션을 실행하려면 백엔드와 프론트엔드 서비스를 각각 설정하고 실행해야 합니다.

### 1. 백엔드 설정 (`backend`)

백엔드는 FastAPI, Celery, PostgreSQL, Docker를 사용합니다. 환경 설정, 의존성 설치 및 서버 실행에 대한 자세한 내용은 해당 디렉토리의 README 파일을 참조하세요.

➡️ **[Backend README](./backend/README.md)**

### 2. 프론트엔드 설정 (`frontend`)

프론트엔드는 React, Vite, TypeScript를 사용합니다. 환경 설정, 의존성 설치 및 개발 서버 시작에 대한 자세한 내용은 해당 디렉토리의 README 파일을 참조하세요.

➡️ **[Frontend README](./frontend/README.md)**

## 🛠️ 기술 스택

### Backend

- **Language**: Python 3.12+
- **Framework**: FastAPI
- **Async Tasks**: Celery, Redis
- **Database**: PostgreSQL, SQLAlchemy, Alembic
- **Dependency Management**: Poetry
- **Containerization**: Docker

### Frontend

- **Core**: React, TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand (Global), React Query (Server)
- **Routing**: React Router
- **HTTP Client**: Axios
- **Package Manager**: Yarn
