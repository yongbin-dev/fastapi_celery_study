pip install -r requirements.txt
python main.py

⏺ 사용 방법

개발 환경 (기본):
python main.py # .env.development 사용

운영 환경:
ENVIRONMENT=production python main.py # .env.production 사용

스테이징 환경:
ENVIRONMENT=staging python main.py # .env.staging 사용

Docker에서 사용

# Dockerfile

ENV ENVIRONMENT=production

기존 .env 파일 처리

기존 .env 파일을 .env.development로 복사하거나 기본 fallback으로 유지할 수 있습니다.

이제 환경에 따라 자동으로 적절한 설정 파일이 로드됩니다!
