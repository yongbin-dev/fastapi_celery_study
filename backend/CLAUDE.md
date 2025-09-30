# CLAUDE.md

이 파일은 이 저장소에서 코드 작업 시 Claude Code (claude.ai/code)에게 가이드를 제공합니다.

## 언어 설정

**중요**: 이 프로젝트에서는 모든 커뮤니케이션을 한국어로 진행합니다. 질문, 답변, 설명, 주석 등 모든 텍스트는 한국어를 사용해 주세요.

## 프로젝트 개요

FastAPI + Celery + React 기반 풀스택 애플리케이션으로, 도메인 중심 아키텍처(Domain-Driven Architecture)를 채택한 AI/ML 마이크로서비스 플랫폼입니다.

## 아키텍처

### Backend: 도메인 중심 아키텍처

```
backend/app/
├── domains/              # 도메인별 기능 모듈 (독립적)
│   ├── llm/             # LLM 관련 기능
│   ├── ocr/             # OCR 관련 기능
│   └── [domain]/        # 각 도메인: controllers, services, tasks, schemas, models
├── orchestration/        # 도메인 간 조율 및 파이프라인
│   ├── controllers/     # 파이프라인 API
│   ├── services/        # 파이프라인 서비스
│   ├── pipelines/       # 파이프라인 정의
│   └── workflows/       # 워크플로우 빌더
├── repository/          # 데이터 액세스 레이어
│   ├── crud/
│   │   ├── async_crud/  # 비동기 CRUD
│   │   └── sync_crud/   # 동기 CRUD (Celery용)
├── shared/              # 공통 모듈
│   ├── base_model.py
│   ├── base_service.py
│   └── redis_service.py
├── core/                # 핵심 인프라
│   ├── database.py      # DB 연결 관리
│   ├── logging.py       # 로깅 설정
│   ├── middleware/      # 미들웨어
│   ├── handler/         # 예외 처리
│   └── celery/          # Celery 설정
├── models/              # SQLAlchemy 모델
├── schemas/             # Pydantic 스키마
└── utils/               # 유틸리티
```

#### 1. 도메인 구조

각 도메인은 동일한 구조를 유지:

```
domains/[domain_name]/
├── __init__.py
├── controllers/      # FastAPI 라우터
├── services/         # 비즈니스 로직
├── tasks/           # Celery 태스크
├── schemas/         # Pydantic 모델
└── models/          # SQLAlchemy 모델 (선택)
```

### pyproject.toml 구조

```toml
[project.optional-dependencies]
dev = ["pytest", "black", ...]
llm = ["torch", "transformers", ...]
ocr = ["easyocr", "paddlepaddle-gpu", ...]
vision = ["ultralytics", "opencv-python", ...]
```

### 로깅

- 모든 중요한 작업에 로깅 추가
- `app.core.logging.get_logger()` 사용
- 적절한 로그 레벨 사용: DEBUG, INFO, WARNING, ERROR, CRITICAL

### 에러 처리

- 모든 외부 API 호출, DB 작업에 try-except 사용
- `ResponseBuilder`를 사용한 일관된 응답 형식
- Celery 태스크는 항상 에러를 캐치하고 로깅

## 주의사항

### 비동기/동기 컨텍스트 분리

- **FastAPI (비동기)**: `async/await`, `get_async_session()` 사용
- **Celery (동기)**: 일반 함수, `get_sync_session()` 사용
