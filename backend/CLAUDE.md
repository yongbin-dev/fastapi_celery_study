# CLAUDE.md

이 파일은 이 저장소에서 코드 작업 시 Claude Code (claude.ai/code)에게 가이드를 제공합니다.

## 언어 설정

**중요**: 이 프로젝트에서는 모든 커뮤니케이션을 한국어로 진행합니다. 질문, 답변, 설명, 주석 등 모든 텍스트는 한국어를 사용해 주세요.

## 프로젝트 개요

FastAPI + Celery + React 기반 풀스택 애플리케이션으로, 도메인 중심 아키텍처(Domain-Driven Architecture)를 채택한 AI/ML 마이크로서비스 플랫폼입니다.

## 아키텍처

### Backend: 도메인 중심 아키텍처

```
backend/
├── app/
│   ├── domains/              # 도메인별 기능 모듈 (독립적)
│   │   ├── common/          # 공통 도메인 (스키마, 서비스)
│   │   │   ├── schemas/     # 파이프라인 관련 공통 스키마
│   │   │   └── services/    # 공통 서비스
│   │   ├── pipeline/        # 파이프라인 도메인 (orchestration 통합)
│   │   │   ├── controllers/ # 파이프라인 API
│   │   │   ├── services/    # 파이프라인 서비스
│   │   │   └── pipelines/   # 파이프라인 정의
│   │   ├── llm/             # LLM 관련 기능
│   │   │   ├── controllers/ # LLM API
│   │   │   ├── services/    # LLM 서비스 (HTTP 클라이언트)
│   │   │   └── schemas/     # LLM 스키마
│   │   └── ocr/             # OCR 관련 기능
│   │       ├── controllers/ # OCR API
│   │       ├── services/    # OCR 서비스 (HTTP 클라이언트)
│   │       └── schemas/     # OCR 스키마
│   ├── repository/          # 데이터 액세스 레이어
│   │   ├── crud/
│   │   │   ├── async_crud/  # 비동기 CRUD
│   │   │   └── sync_crud/   # 동기 CRUD (Celery용)
│   ├── shared/              # 공통 모듈
│   │   ├── base_model.py
│   │   ├── base_service.py
│   │   └── redis_service.py
│   ├── core/                # 핵심 인프라
│   │   ├── database.py      # DB 연결 관리
│   │   ├── logging.py       # 로깅 설정
│   │   ├── middleware/      # 미들웨어
│   │   ├── handler/         # 예외 처리
│   │   └── celery/          # Celery 설정
│   ├── models/              # SQLAlchemy 모델
│   ├── schemas/             # Pydantic 스키마
│   └── utils/               # 유틸리티
└── model_servers/           # 독립 모델 서버 (마이크로서비스)
    └── ocr_server/          # OCR 모델 서버
        ├── engines/         # OCR 엔진 구현
        ├── models/          # 모델 관리
        └── server.py        # FastAPI 서버
```

#### 1. 도메인 구조

각 도메인은 목적에 맞게 구조화:

```
domains/common/           # 공통 도메인
├── schemas/             # 파이프라인, 체인 실행, 태스크 로그 스키마
└── services/            # 공통 서비스

domains/pipeline/        # 파이프라인 도메인 (orchestration 통합)
├── controllers/         # 파이프라인 API 엔드포인트
├── services/           # 파이프라인 실행 서비스
└── pipelines/          # AI 파이프라인 정의

domains/llm/            # LLM 도메인
├── controllers/        # LLM API 엔드포인트
├── services/          # LLM 서비스 (모델 서버 HTTP 클라이언트)
├── schemas/           # 요청/응답 스키마
└── models/            # (선택) SQLAlchemy 모델

domains/ocr/            # OCR 도메인
├── controllers/        # OCR API 엔드포인트
├── services/          # OCR 서비스 (모델 서버 HTTP 클라이언트)
│   └── similarity/    # 유사도 계산 서비스
└── schemas/           # 요청/응답 스키마
```

#### 2. 모델 서버 구조

AI/ML 모델은 독립적인 마이크로서비스로 분리:

```
model_servers/ocr_server/
├── engines/             # OCR 엔진 구현체
│   ├── base.py         # 기본 인터페이스
│   ├── easyocr_engine.py
│   ├── paddleocr_engine.py
│   ├── mock_engine.py
│   └── factory.py      # 엔진 팩토리
├── models/             # 모델 관리
├── ocr_model.py        # OCR 모델 래퍼
├── server.py           # FastAPI 서버
└── Dockerfile          # 독립 배포
```

**주요 특징**:
- FastAPI 기반 독립 HTTP 서버
- GPU/CPU 별도 컨테이너 지원
- 메인 앱과 독립적인 스케일링
- 모델 로딩/추론 최적화

#### 3. 아키텍처 변경 사항

**통신 구조**:
```
Client → FastAPI (domains/*/controllers)
         ↓
    Services (domains/*/services)
         ↓ HTTP
    Model Servers (model_servers/*/server.py)
         ↓
    AI/ML Models (GPU/CPU)
```

### pyproject.toml 구조

```toml
[project.optional-dependencies]
dev = ["pytest", "black", ...]
llm = ["torch", "transformers", ...]  # 모델 서버용
ocr = ["easyocr", "paddlepaddle-gpu", ...]  # 모델 서버용
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

### 모델 서버 통신

- 도메인 서비스는 모델 서버와 **HTTP 통신**만 수행
- 모델 로딩/추론은 모델 서버에서만 처리
- 타임아웃 설정: 모델 추론 시간 고려 (기본 30-60초)
- 에러 처리: 모델 서버 장애 시 적절한 fallback 또는 재시도

### 도메인 독립성

- 각 도메인은 독립적으로 동작 가능해야 함
- 도메인 간 직접 의존성 최소화
- 공통 기능은 `domains/common/` 또는 `shared/` 사용
- 파이프라인은 `domains/pipeline/`에서 도메인 간 조율
