# API Server Dockerfile
# FastAPI 기반 REST API 서버

FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# UV 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# shared 패키지 먼저 복사
COPY packages/shared /app/shared

# 의존성 파일 복사
COPY packages/api_server/pyproject.toml ./

# 가상환경 생성 및 모든 의존성 설치 (shared 포함)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --python 3.12 --no-dev

# celery_worker의 tasks 모듈 복사 (Celery 태스크 호출용)
COPY packages/celery_worker/tasks /app/tasks
COPY packages/celery_worker/core /app/core
COPY packages/celery_worker/celery_app.py /app/celery_app.py

# 소스 코드 복사
COPY packages/api_server/app ./app
COPY packages/api_server/main.py ./main.py

# 환경 변수
ENV PYTHONPATH=/app \
    TZ=Asia/Seoul

# 포트 노출
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 컨테이너 시작
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
