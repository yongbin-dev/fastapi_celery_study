# config.py
import os
from typing import List
from pydantic_settings import BaseSettings

# 환경에 따른 .env 파일 결정
def get_env_file():
    env = os.getenv("ENVIRONMENT", "development")
    return f".env.{env}"

class Settings(BaseSettings):
    # 환경 설정
    environment: str = "development"

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
    EXCLUDE_PATHS: List[str] = [
        "/docs",
        "/openapi.json",
        "/favicon.ico",
        "/health"
    ]

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
    
    # Database 설정
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/dbname"
    DB_ECHO: bool = False  # SQL 쿼리 로깅 활성화/비활성화
    
    # Pipeline 설정
    PIPELINE_TTL: int = 3600  # Redis에서 파이프라인 데이터 TTL (초)
    
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
    
    # JWT 인증 설정
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24시간
    
    # AI/ML 설정
    HUGGINGFACE_CACHE_DIR: str = "./cache/huggingface"
    MODEL_CACHE_SIZE: int = 1000
    
    # 개발 도구
    ENABLE_RELOAD: bool = True
    ENABLE_DOCS: bool = True


    class Config:
        env_file = get_env_file()
        env_file_encoding = "utf-8"

# 전역 설정 객체
settings = Settings()