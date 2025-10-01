## 일반적인 개발 명령어

### 환경 설정

#### 기본 설치

- **개발 환경 (CPU)**: `uv sync --extra dev` - 개발 의존성 + OCR CPU 버전 포함
- **운영 환경 (GPU)**: `uv sync --extra prod` - 운영 의존성 + OCR GPU 버전 포함
- **LLM 도메인**: `uv sync --extra llm` - LLM 관련 의존성 설치
- **Vision 도메인**: `uv sync --extra vision` - Vision 관련 의존성 설치

#### OCR 환경별 설치

> **중요**: PaddleOCR과 EasyOCR은 환경(CPU/GPU)에 따라 다른 의존성이 필요합니다.

- **개발 환경 (CPU)**:
  - `uv sync --extra dev` - PaddlePaddle CPU 버전 포함
  - 또는 개별 설치: `uv sync --extra ocr-base --extra ocr-cpu`

- **운영 환경 (GPU)**:
  - `uv sync --extra prod` - PaddlePaddle GPU 버전 포함
  - 또는 개별 설치: `uv sync --extra ocr-base --extra ocr-gpu`

- **OCR 기본 의존성만**: `uv sync --extra ocr-base` - OpenCV, Pillow 등

#### Docker

- **Docker**: `docker-compose up` - 모든 서비스 시작 (app, Redis, Celery worker, Flower)

### 개발

- **로컬 실행**: `uv run python -m app.main` 또는 `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 5050`
- **환경별 실행**: `ENVIRONMENT=production uv run python -m app.main`
- **Celery Worker**: `uv run celery -A app.core.celery_app worker --loglevel=info --logfile=logs/celery_worker_$(date +%Y-%m-%d).log`
- **Flower (Celery 모니터링)**: `uv run celery -A app.core.celery_app flower --port=5555`

### 코드 품질

- **포맷팅**: `uv run black .` - 코드 포맷팅
- **린트**: `uv run flake8` - 코드 린트
- **타입 검사**: `uv run mypy .` - 정적 타입 검사
- **테스트**: `uv run pytest` - 모든 테스트 실행
- **개별 테스트**: `uv run pytest tests/test_specific.py` - 특정 테스트 파일 실행

### Docker 작업

- **빌드**: `docker-compose build`
- **서비스 시작**: `docker-compose up -d`
- **로그 확인**: `docker-compose logs -f app`
- **중지**: `docker-compose down`

## 아키텍처 개요

백그라운드 작업 처리를 위한 Celery가 포함된 FastAPI 기반 마이크로서비스입니다:

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
- PyTorch: 개발환경은 CPU, 운영환경은 CUDA 지원
- `app/services/ai/`에서 모델 서비스 추상화

## 환경 설정

애플리케이션은 환경별 .env 파일을 통해 다중 환경을 지원합니다:

- `.env.development` (기본값)
- `.env.production`
- `.env.staging`

설정을 전환하려면 `ENVIRONMENT` 변수를 설정하세요.

## 패키지 관리 (uv)

이 프로젝트는 **uv**를 사용하여 패키지를 관리합니다.

### uv 설치

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 의존성 설치

```bash
# 기본 의존성만 설치
uv sync

# 개발 환경 (CPU) - 권장
uv sync --extra dev

# 운영 환경 (GPU) - 권장
uv sync --extra prod

# 여러 그룹 동시 설치
uv sync --extra dev --extra llm --extra ocr-base --extra ocr-cpu

# 운영 환경에서 LLM + OCR (GPU)
uv sync --extra prod --extra llm --extra ocr-base --extra ocr-gpu
```

### 새 패키지 추가

```bash
# 기본 의존성에 추가
uv add fastapi

# 개발 의존성에 추가
uv add --dev pytest

# 특정 그룹에 추가
uv add --optional llm transformers
```
