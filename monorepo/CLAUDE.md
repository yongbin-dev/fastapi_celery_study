## 언어 설정

**중요**: 이 프로젝트에서는 모든 커뮤니케이션을 한국어로 진행합니다. 질문, 답변, 설명, 주석 등 모든 텍스트는 한국어를 사용해 주세요.

## 프로젝트 개요

이 프로젝트는 **uv 워크스페이스 기반 Python 모노레포**로, FastAPI + Celery + ML 서버로 구성된 마이크로서비스 아키텍처입니다.

### 패키지 구조

```
packages/
├── shared/          # 공통 라이브러리 (모든 패키지가 의존)
├── api_server/      # FastAPI 기반 REST API 서버
├── celery_worker/   # Celery 백그라운드 작업 워커
└── ml_server/       # AI/ML 모델 서버 (OCR 등)
```

### 패키지 의존성

- **shared**: 공통 유틸리티, 모델, CRUD, 설정, 미들웨어

  - `config/`: 환경 설정 (settings.py)
  - `models/`: SQLAlchemy 모델
  - `schemas/`: Pydantic 스키마 (OCRTextBoxCreate, ChainExecution, StageSchema 등)
  - `repository/crud/`: 동기/비동기 CRUD 작업
  - `core/`: 데이터베이스, Redis, Supabase, 로깅
  - `middleware/`: 요청/응답 로깅
  - `handler/`: 예외 처리 핸들러
  - `pipeline/`: 파이프라인 공통 유틸리티
  - `service/`: 공통 서비스 레이어
  - `utils/`: 유틸리티 함수

- **api_server**: REST API 서버 (shared 의존)

  - 도메인 중심 아키텍처: `app/domains/{ocr,llm,pipeline}/`
  - 각 도메인: `controllers/`, `services/`, `schemas/`
  - Repository 패턴: shared 패키지의 CRUD 사용

- **celery_worker**: 백그라운드 작업 워커 (shared 의존)

  - `core/`: Celery 설정 및 태스크 데코레이터
  - `tasks/`: 실제 작업 정의
    - `stages/`: 스테이지별 태스크 구성 (OCR, LLM 등)
    - `pipeline_tasks.py`: 파이프라인 오케스트레이션

- **ml_server**: ML 모델 추론 서버 (독립 실행)
  - `domains/`: 도메인별 구성 (ocr 등)
  - `engines/`: OCR 엔진 (EasyOCR, PaddleOCR, Mock)
  - `llm_engines/`: LLM 엔진
  - `models/`: 데이터 모델
  - `core/`: 서버 설정 및 의존성
  - Factory 패턴으로 엔진 선택

## 가상환경 관리

**중요**: 이 프로젝트는 **루트 디렉토리의 통합 가상환경**(.venv)을 사용합니다.

### VSCode 설정

- `.vscode/monorepo.code-workspace` 로 vscode의 작업환경 구성

## 로깅 시스템

**패키지별 로그 디렉토리 자동 분리**:
- 각 패키지는 `logs/{package_name}/` 디렉토리에 로그 저장
- 현재 로그: `logs/api_server/`
- 로그 파일명: 타임스탬프 기반 자동 생성

## 주요 아키텍처 특징

### 스키마 통일
- OCR 관련 스키마: `OCRTextBoxCreate`, `OCRTextBoxRead` 등으로 통일
- 공통 응답 스키마: `ResponseModel`, `PaginatedResponse`
- 체인 실행 스키마: `ChainExecution`, `StageSchema`

### 파이프라인 아키텍처
- 스테이지 기반 파이프라인 실행
- 각 스테이지는 독립적인 Celery 태스크
- 파이프라인 상태 추적 및 재시도 메커니즘

### 예외 처리 구조
- 공통 예외 핸들러: `shared/handler/`
- 도메인별 예외 클래스
- 일관된 에러 응답 포맷
