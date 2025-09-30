
FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성 설치 (OCR, CV 라이브러리용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 의존성 파일 복사 (캐시 최적화)
COPY pyproject.toml uv.lock README.md ./

# 의존성 설치 (운영 + OCR)
RUN uv sync --extra prod --extra ocr --no-dev

# 소스코드 복사
COPY . .

# 환경변수 설정
ENV WORKERS=1
ENV PYTHONPATH=/app
ENV TORCH_THREADS=1
ENV HOST=0.0.0.0
ENV PORT=5050

# PaddlePaddle CPU 최적화 설정
ENV FLAGS_use_mkldnn=0
ENV KMP_DUPLICATE_LIB_OK=TRUE

# 포트 노출
EXPOSE 5050

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5050/health || exit 1

# 기본 명령어 (uvicorn)
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port 5050"]