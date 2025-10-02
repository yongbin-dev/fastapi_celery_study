# app/main.py (개선 버전)

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import close_db, init_db
from app.core.handler.exceptions_handler import setup_exception_handlers
from app.core.middleware.request_middleware import RequestLogMiddleware
from app.core.middleware.response_middleware import ResponseLogMiddleware
from app.core.router import api_router
from app.utils.response_builder import ResponseBuilder


# 애플리케이션 시작/종료 이벤트 처리
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행

    # 타임존을 서울로 설정
    os.environ["TZ"] = "Asia/Seoul"
    import time

    time.tzset()  # Unix/Linux에서 타임존 설정 적용

    logger.info("🚀 FastAPI 애플리케이션 시작")
    logger.info("🕐 타임존 설정: Asia/Seoul")
    logger.info(f"📋 설정: {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"🌐 서버: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"📚 API 문서: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"🌐 CORS Origins: {settings.BACKEND_CORS_ORIGINS}")

    # 데이터베이스 초기화 (선택사항)
    try:
        await init_db()
        logger.info("✅ 데이터베이스 연결 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        logger.error("💥 DB 연결 없이는 애플리케이션을 시작할 수 없습니다. 종료합니다.")
        # DB 필수인 경우 애플리케이션 종료
        import sys

        sys.exit(1)

    yield  # 애플리케이션 실행

    # 종료 시 실행
    logger.info("🛑 FastAPI 애플리케이션 종료")

    # 데이터베이스 연결 종료
    try:
        await close_db()
        logger.info("✅ 데이터베이스 연결 종료 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 지우연결 종료 실패: {e}")


# 로깅 초기화
from app.core.logging import get_logger  # noqa: E402

logger = get_logger(__name__)

# FastAPI 앱 생성

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="공통 응답 형식을 사용하는 FastAPI 애플리케이션",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# 미들웨어 등록 (순서 중요: 역순으로 실행됨)
def setup_middleware():
    """미들웨어 설정"""

    app.add_middleware(ResponseLogMiddleware)
    # Request/Response 로깅 미들웨어
    app.add_middleware(RequestLogMiddleware)
    # CORS 미들웨어 (가장 먼저 실행되어야 함)
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("✅ 미들웨어 설정 완료")


# 라우터 설정
def setup_routers():
    """라우터 설정"""
    # API 라우터 등록
    app.include_router(api_router, prefix=settings.API_V1_STR, tags=["API v1"])

    logger.info(f"✅ 라우터 설정 완료 - Prefix: {settings.API_V1_STR}")


# 기본 엔드포인트들
@app.get("/", tags=["Root"])
async def root():
    """루트 엔드포인트"""
    return ResponseBuilder.success(
        data={
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/health",
        },
        message="API 서버가 정상 작동 중입니다",
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """헬스체크 엔드포인트"""
    return ResponseBuilder.success(
        data={
            "status": "healthy",
            "version": settings.VERSION,
            "environment": "development",  # 환경에 따라 변경
        },
        message="서버 상태 정상",
    )


@app.get("/version", tags=["Info"])
async def get_version():
    """버전 정보"""
    return ResponseBuilder.success(
        data={
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "api_version": "v1",
        },
        message="버전 정보",
    )


# 애플리케이션 설정 초기화
def create_application() -> FastAPI:
    """애플리케이션 생성 및 설정"""
    setup_middleware()
    setup_exception_handlers(app)
    setup_routers()
    logger.info("🎉 FastAPI 애플리케이션 설정 완료")
    return app


# 애플리케이션 초기화 실행
create_application()
