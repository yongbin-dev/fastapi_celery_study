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

# 의존성 파일 먼저 복사 (캐싱 최적화)
COPY pyproject.toml uv.lock ./
COPY packages/shared/pyproject.toml ./packages/shared/
COPY packages/celery_worker/pyproject.toml ./packages/celery_worker/

# 의존성 설치 (워크스페이스 기반)
RUN uv sync --frozen --no-dev

# 소스 코드 복사
COPY packages/shared/ ./packages/shared/
COPY packages/celery_worker/ ./packages/celery_worker/

# 실행 단계
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# 런타임 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 빌드 단계에서 가상환경과 소스 복사
COPY --from=base /app/.venv /app/.venv
COPY --from=base /app/packages /app/packages

# 비특권 사용자 생성 및 전환
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Celery 워커 실행
WORKDIR /app/packages/celery_worker
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]
