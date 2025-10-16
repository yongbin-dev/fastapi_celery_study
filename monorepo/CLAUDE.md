# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
  - `schemas/`: Pydantic 스키마
  - `repository/crud/`: 동기/비동기 CRUD 작업
  - `core/`: 데이터베이스, Redis, Supabase, 로깅
  - `middleware/`: 요청/응답 로깅
  - `exceptions/`: 예외 처리

- **api_server**: REST API 서버 (shared 의존)
  - 도메인 중심 아키텍처: `app/domains/{ocr,llm,pipeline,common}/`
  - 각 도메인: `controllers/`, `services/`, `schemas/`
  - Repository 패턴: `app/repository/crud/`

- **celery_worker**: 백그라운드 작업 워커 (shared 의존)
  - `core/`: Celery 설정 및 태스크 데코레이터
  - `tasks/`: 실제 작업 정의 (pipeline_tasks.py)

- **ml_server**: ML 모델 추론 서버 (독립 실행)
  - OCR 엔진: EasyOCR, PaddleOCR, Mock 엔진 지원
  - Factory 패턴으로 엔진 선택

## 개발 명령어

### 패키지 관리 (uv)

```bash
# 의존성 설치
uv sync

# 특정 패키지에 의존성 추가
cd packages/api_server
uv add <package-name>

# 개발 의존성 추가
uv add --dev <package-name>
```

### 코드 품질 도구

```bash
# Ruff 린트 실행 (프로젝트 루트에서)
uv run ruff check packages/

# Ruff 자동 수정
uv run ruff check --fix packages/

# Pyright 타입 체크
uv run pyright

# 모든 체크 한번에 실행
uv run ruff check packages/ && uv run pyright
```

## 아키텍처 특징

### 1. 도메인 중심 설계 (API 서버)

API 서버는 도메인별로 코드를 구조화합니다:

- **controllers/**: FastAPI 라우터 및 엔드포인트
- **services/**: 비즈니스 로직 (도메인 서비스)
- **schemas/**: 요청/응답 Pydantic 모델
- **models/**: SQLAlchemy ORM 모델 (shared에 정의)

예시: OCR 도메인
```
app/domains/ocr/
├── controllers/     # API 엔드포인트
│   ├── ocr_controller.py
│   └── comparison_controller.py
├── services/        # 비즈니스 로직
│   ├── ocr_service.py
│   ├── ocr_comparison_service.py
│   └── similarity/  # 유사도 계산 알고리즘
└── schemas/         # 데이터 스키마
    ├── request.py
    ├── response.py
    └── similarity.py
```

### 2. Repository 패턴

데이터베이스 작업은 Repository 패턴으로 추상화되어 있습니다:

- **sync_crud/**: 동기 CRUD 작업
- **async_crud/**: 비동기 CRUD 작업 (AsyncSession 사용)
- **base.py**: 공통 CRUD 메서드 (Create, Read, Update, Delete)

각 모델별 CRUD 클래스:
- `TaskLogCRUD`, `ChainExecutionCRUD`, `OCRExecutionCRUD`, `OCRTextBoxCRUD`

### 3. 공통 응답 형식

모든 API 응답은 `ResponseBuilder`를 통해 통일된 형식으로 반환됩니다:

```python
from shared.utils.response_builder import ResponseBuilder

# 성공 응답
return ResponseBuilder.success(
    data={"key": "value"},
    message="작업 완료"
)

# 에러 응답
return ResponseBuilder.error(
    message="작업 실패",
    errors=["상세 에러"]
)
```

### 4. 환경 설정

환경별 설정은 `.env.{environment}` 파일로 관리됩니다:
- `.env.development`
- `.env.production`

`ENVIRONMENT` 환경 변수로 파일 선택:
```bash
export ENVIRONMENT=production
```

주요 설정 (`shared/config/settings.py`):
- 데이터베이스: PostgreSQL + asyncpg
- 캐시/메시지 브로커: Redis
- 스토리지: Supabase Storage
- ML 서버 URL: `OCR_MODEL_SERVER_URL`

### 5. 미들웨어 구조

- **RequestLogMiddleware**: 요청 로깅 및 타이밍
- **ResponseLogMiddleware**: 응답 로깅
- **Exception Handler**: 전역 예외 처리 (공통 응답 형식 반환)

## 개발 가이드라인

### 새로운 도메인 추가 시

1. `app/domains/{domain_name}/` 디렉토리 생성
2. `controllers/`, `services/`, `schemas/` 하위 디렉토리 구성
3. 필요한 경우 `shared/models/`에 SQLAlchemy 모델 추가
4. 필요한 경우 `shared/repository/crud/`에 CRUD 클래스 추가
5. `app/main.py`의 `setup_routers()`에서 라우터 등록

### 새로운 Celery 작업 추가 시

1. `packages/celery_worker/tasks/`에 작업 모듈 추가
2. `@task_with_context` 데코레이터 사용 (로깅/예외처리 자동화)
3. `celery_app.py`에서 작업 자동 탐색 활성화됨

### 데이터베이스 모델 변경 시

1. `shared/models/`에서 모델 수정
2. Alembic 마이그레이션 생성 필요 (현재 설정되어 있지 않음)
3. 모델 변경 시 관련 CRUD 클래스도 업데이트

### 타입 체크 및 린트

- **Python 3.12+** 타입 힌트 사용
- Ruff 규칙 준수: E, F, I, N, W
- Pyright `basic` 모드로 타입 체크
- 라인 길이: 88자

## 주의사항

- **모든 패키지는 shared에 의존**: shared 변경 시 영향 범위 확인 필요
- **비동기/동기 혼용**: API 서버는 비동기, Celery는 동기 패턴 사용
- **데이터베이스 연결**: API 서버는 asyncpg, Celery/CRUD는 psycopg2
- **타임존**: 모든 서버는 `Asia/Seoul` 타임존 사용
