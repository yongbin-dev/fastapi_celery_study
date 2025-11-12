# config.py
import os
from typing import List
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings

from ..core.logging import get_logger  # noqa: E402

logger = get_logger(__name__)


# 환경에 따른 .env 파일 결정
def get_env_file():
    env = os.getenv("ENVIRONMENT", "development")
    return f".env.{env}"


class Settings(BaseSettings):
    # 환경 설정
    ENVIRONMENT: str = "development"  # 대문자로 변경하여 환경변수와 매칭

    # API 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Common Response"
    VERSION: str = "1.0.0"

    # CORS 설정
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # 제외할 경로
    EXCLUDE_PATHS: List[str] = ["/docs", "/openapi.json", "/favicon.ico", "/health"]

    # 응답 설정
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_RESPONSE_BODY_LOGGING: bool = False
    MAX_RESPONSE_BODY_SIZE: int = 1000

    # FastAPI 설정
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Redis/Celery 설정
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: str = "0"

    # Database 설정
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/dbname"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/dbname"

    NEXT_PUBLIC_SUPABASE_URL: str = ""
    NEXT_PUBLIC_SUPABASE_ANON_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "yb_test_storage"  # Supabase Storage 버킷 이름
    SUPABASE_STORAGE_PATH: str = "uploads"  # 버킷 내 저장 경로
    DB_ECHO: bool = False  # SQL 쿼리 로깅 활성화/비활성화
    DB_POOL_SIZE: int = 5  # 데이터베이스 연결 풀 크기 (Celery 환경에서는 작게 설정)
    DB_MAX_OVERFLOW: int = 10  # 추가 연결 허용 개수 (피크 시 대응)
    DB_TIMEZONE: str = "Asia/Seoul"  # 데이터베이스 시간대
    DB_POOL_PRE_PING: bool = True  # 연결 유효성 검사
    DB_POOL_RECYCLE: int = 1800  # 연결 재활용 시간(초) - 30분
    DB_CONNECT_TIMEOUT: int = 30  # 연결 타임아웃(초)
    DB_HEALTH_CHECK_POOL_SIZE: int = 2  # 헬스체크용 별도 풀 크기 (최소화)

    # Pipeline 설정
    PIPELINE_TTL: int = 3600  # Redis에서 파이프라인 데이터 TTL (초)

    # 파일 업로드 설정
    MAX_PDF_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB (bytes)
    ALLOWED_PDF_CONTENT_TYPES: List[str] = ["application/pdf"]

    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True
    DEBUG: bool = False
    ENABLE_JSON_LOGS: bool = False

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 5050

    # Redis 인증
    REDIS_PASSWORD: str = ""

    # Celery 설정
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_MODULES: List[str] = [
        "app.core.celery.celery_tasks"
    ]  # 동적 태스크 모듈 설정

    # JWT 인증 설정
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24시간

    # AI/ML 설정
    HUGGINGFACE_CACHE_DIR: str = "./cache/huggingface"
    MODEL_CACHE_SIZE: int = 1000

    # Ollama 설정
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # 개발 도구
    ENABLE_RELOAD: bool = True
    ENABLE_DOCS: bool = True

    model_config = {"env_file": get_env_file(), "env_file_encoding": "utf-8"}
    OCR_ENGINE: str = "easyocr"
    OCR_DET: str = ""
    OCR_REC: str = ""
    OCR_USE_ANGLE_CLS: bool = True  # OCR 각도 보정 사용 여부
    OCR_LANG: str = "korean"  # OCR 기본 언어

    # 모델 서버 설정
    MODEL_SERVER_URL: str = "http://localhost:8002/api/model"  # OCR 전용 서버 URL
    MODEL_SERVER_TIMEOUT: int = 60
    ML_SERVER_PORT: int = 8002
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    USE_GRPC: str = "true"
    GRPC_PORT: int = 50051
    ML_SERVER_GRPC_ADDRESS: str = "localhost:50051"
    ML_SERVER_BENTO_ADDRESS: str = "localhost:50052"

    # CELERY Worker 설정
    # Pool 타입:
    #   - solo: 디버깅용 (1개씩 순차 실행, GPU 메모리 효율적)
    #   - prefork: GPU 사용 시 권장 (프로세스 격리, concurrency=1-2)
    #   - gevent: I/O 작업용 (GPU 작업과 호환 불가)
    #   - threads: 멀티스레드 (GPU 작업 비권장)
    CELERY_WORKER_POOL: str = "prefork"
    CELERY_WORKER_CONCURRENCY: int = 1
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 100
    CELERY_WORKER_LOGLEVEL: str = "INFO"

    @model_validator(mode="after")
    def set_redis_details_from_url(self) -> "Settings":
        """
        Parse REDIS_HOST and REDIS_PORT from REDIS_URL.
        """
        if self.REDIS_URL:
            parsed_url = urlparse(self.REDIS_URL)
            self.REDIS_HOST = parsed_url.hostname or "localhost"
            self.REDIS_PORT = parsed_url.port or 6379
            if parsed_url.path:
                # /0 -> 0
                self.REDIS_DB = parsed_url.path.lstrip("/")
        return self


# 전역 설정 객체
settings = Settings()

# 환경 로깅
logger.info(f"📡 환경: {settings.ENVIRONMENT}")
