# Celery Worker Dockerfile
# 백그라운드 작업 처리 워커

FROM python:3.12-slim AS base

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 작업 디렉토리 설정
WORKDIR /app

# shared의 pyproject.toml 먼저 복사 (의존성 변경 감지)
COPY packages/shared/pyproject.toml /app/shared/pyproject.toml

# celery_worker 의존성 파일 복사
COPY packages/celery_worker/pyproject.toml ./

# celery_worker 패키지 의존성만 설치 (CUDA 없음)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --python 3.12 --no-dev

# shared 전체 복사 (소스 코드 변경 감지)
COPY packages/shared /app/shared

# shared 재설치 (editable 모드, 항상 재설치)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --force-reinstall --no-deps -e /app/shared

# celery_worker 소스 코드 복사
COPY packages/celery_worker/ ./celery_worker/

# 실행 단계
FROM python:3.12-slim AS runtime

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:/app/shared:/app/celery_worker" \
    SERVICE_NAME=celery_worker \
    CELERY_LOG_LEVEL=info \
    CELERY_CONCURRENCY=4

# 런타임 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 빌드 단계에서 가상환경과 소스 복사
COPY --from=base /app/.venv /app/.venv
COPY --from=base /app/shared /app/shared
COPY --from=base /app/celery_worker /app/celery_worker

# 비특권 사용자 생성 및 로그 디렉토리 생성
# logging.py에서 계산하는 경로: /logs/celery_worker/
RUN useradd -m -u 1000 appuser && \
    mkdir -p /logs/celery_worker && \
    mkdir -p /app/logs/celery_worker && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /logs

USER appuser

# Celery 워커 작업 디렉토리
WORKDIR /app/celery_worker

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD celery -A celery_app inspect ping -d celery@$HOSTNAME || exit 1

# Celery 워커 실행 (환경 변수로 제어 가능)
CMD ["sh", "-c", "celery -A celery_app worker --loglevel=$CELERY_LOG_LEVEL --concurrency=$CELERY_CONCURRENCY"]
