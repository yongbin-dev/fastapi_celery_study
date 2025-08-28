# CLAUDE.md

이 파일은 이 저장소에서 코드 작업 시 Claude Code (claude.ai/code)에게 가이드를 제공합니다.

## 언어 설정
**중요**: 이 프로젝트에서는 모든 커뮤니케이션을 한국어로 진행합니다. 질문, 답변, 설명, 주석 등 모든 텍스트는 한국어를 사용해 주세요.

## 일반적인 개발 명령어

### 환경 설정
- **Poetry**: `poetry install` - 의존성 설치
- **Docker**: `docker-compose up` - 모든 서비스 시작 (app, Redis, Celery worker, Flower)

### 개발
- **로컬 실행**: `python -m app.main` 또는 `uvicorn app.main:app --reload --host 0.0.0.0 --port 5050`
- **환경별 실행**: `ENVIRONMENT=production python -m app.main`
- **Celery Worker**: `python -m celery -A app.core.celery_app worker --loglevel=info`
- **Flower (Celery 모니터링)**: `python -m celery -A app.core.celery_app flower --port=5555`

### 코드 품질
- **포맷팅**: `black .` - 코드 포맷팅
- **린트**: `flake8` - 코드 린트
- **타입 검사**: `mypy .` - 정적 타입 검사
- **테스트**: `pytest` - 모든 테스트 실행
- **개별 테스트**: `pytest tests/test_specific.py` - 특정 테스트 파일 실행

### Docker 작업
- **빌드**: `docker-compose build`
- **서비스 시작**: `docker-compose up -d`
- **로그 확인**: `docker-compose logs -f app`
- **중지**: `docker-compose down`

## 아키텍처 개요

백그라운드 작업 처리를 위한 Celery가 포함된 FastAPI 기반 마이크로서비스입니다:

### 핵심 구조
- **app/main.py**: 미들웨어, CORS, 생명주기 관리가 포함된 FastAPI 애플리케이션 진입점
- **app/core/**: 설정, Celery 설정, 공유 예외
- **app/api/v1/**: `/api/v1` 하위의 버전별 API 라우트
- **app/services/**: AI 모델 서비스 및 작업 처리를 포함한 비즈니스 로직
- **app/schemas/**: 요청/응답 검증을 위한 Pydantic 모델
- **app/middleware/**: 요청/응답 로깅을 위한 커스텀 미들웨어
- **app/utils/response_builder.py**: 표준화된 응답 포맷팅

### 주요 구성 요소
- **응답 시스템**: 모든 엔드포인트에서 일관된 JSON 응답을 위해 `ResponseBuilder` 사용
- **환경 설정**: 다중 환경 지원 (.env.development, .env.production, .env.staging)
- **Celery 통합**: Redis를 브로커로 하는 백그라운드 작업 처리
- **Docker 다중 서비스**: App, Redis, Celery worker, Flower 모니터링

### 서비스 아키텍처
- **FastAPI App** (포트 5050): 메인 API 서버
- **Redis** (포트 6379): 메시지 브로커 및 결과 백엔드
- **Celery Worker**: 백그라운드 작업 처리기
- **Flower** (포트 5555): Celery 작업 모니터링 UI

### AI/ML 통합
- 모델 관리를 위한 Transformers 및 HuggingFace Hub 사용
- 추론을 위한 PyTorch CPU 전용
- `app/services/ai/`에서 모델 서비스 추상화

## 환경 설정

애플리케이션은 환경별 .env 파일을 통해 다중 환경을 지원합니다:
- `.env.development` (기본값)
- `.env.production` 
- `.env.staging`

설정을 전환하려면 `ENVIRONMENT` 변수를 설정하세요.