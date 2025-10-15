# Dockerfile - OCR Model Server
FROM backend-ml-gpu-base:latest

WORKDIR /app

# 기존 앱 코드 복사 (모델 로직 재사용)
# 모델 서버 코드 복사
COPY model_servers/ocr_server /model_server

# 모델 서버 실행
WORKDIR /model_server
CMD ["python", "server.py"]
