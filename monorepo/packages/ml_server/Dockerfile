# Dockerfile.ocr-cpu - OCR CPU 버전 (ml-base 기반)
# ml-base에 paddlepaddle + paddleocr + easyocr 추가

FROM backend-ml-base:latest

WORKDIR /app

# 1. 빌드 인수
ARG DOMAIN_EXTRA=ocr-cpu

# 2. OCR 전용 의존성 설치 (캐시 활용)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --extra ${DOMAIN_EXTRA} --no-dev

# 3. shared 패키지 다시 editable mode로 설치
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -e /app/shared

# 4. 소스 코드 복사
COPY ml_server/app ./app

# 5. 환경 변수
ENV FLAGS_use_gpu=False

# 6. 컨테이너 시작
CMD ["sh", "-c", "/app/.venv/bin/uvicorn app.main:app --host ${HOST} --port ${PORT}"]