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

# 의존성 파일 복사
COPY api_server/pyproject.toml ./

# 공통 의존성 설치 (캐시 활용)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --python 3.12 --no-dev

# shared 패키지 복사 및 설치
COPY shared /app/shared
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -e /app/shared

# 소스 코드 복사
COPY api_server/app ./app

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
