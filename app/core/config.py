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

    # Kafka 설정
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "ai-service-group"
    kafka_auto_offset_reset: str = "earliest"


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

    class Config:
        env_file = get_env_file()
        env_file_encoding = "utf-8"

# 전역 설정 객체
settings = Settings()