
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치 (PyTorch, ML 라이브러리용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install poetry

# Poetry 설정 (가상환경 생성 안함)
RUN poetry config virtualenvs.create false

# 의존성 파일 복사 (캐시 최적화)
COPY pyproject.toml poetry.lock ./

# 의존성 설치 (운영 환경만)
RUN poetry install --only=main --no-root

# PyTorch CPU 버전 설치 (M1 Mac 호환성)
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 소스코드 복사
COPY . .

# 환경변수 설정
ENV ENVIRONMENT=production
ENV WORKERS=1
ENV PYTHONPATH=/app
ENV TORCH_THREADS=1

# 포트 노출
EXPOSE 5050

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/ || exit 1

# 운영환경용 gunicorn 실행
CMD ["sh", "-c", "gunicorn main:app -w $WORKERS -k uvicorn.workers.UvicornWorker --bind $HOST:$PORT --timeout 120 --max-requests 1000 --max-requests-jitter 100"]