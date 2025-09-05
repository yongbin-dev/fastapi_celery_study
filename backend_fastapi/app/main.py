# app/main.py (개선 버전)

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import api_router
from .core.config import settings
from .core.database import init_db, close_db
from .handlers.exception_handlers import setup_exception_handlers
from .middleware.response_middleware import ResponseLogMiddleware
from .utils.response_builder import ResponseBuilder


# 애플리케이션 시작/종료 이벤트 처리
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("🚀 FastAPI 애플리케이션 시작")
    logger.info(f"📋 설정: {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"🌐 CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
    
    # 데이터베이스 초기화 (선택사항)
    # try:
    #     await init_db()
    #     logger.info("✅ 데이터베이스 연결 초기화 완료")
    # except Exception as e:
    #     logger.error(f"❌ 데이터베이스 연결 실패: {e}")

    yield  # 애플리케이션 실행

    # 종료 시 실행
    logger.info("🛑 FastAPI 애플리케이션 종료")
    
    # 데이터베이스 연결 종료
    try:
        await close_db()
        logger.info("✅ 데이터베이스 연결 종료 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 지우연결 종료 실패: {e}")


# 로그 설정 함수
def setup_logging():
    """로깅 설정 초기화"""
    # logs 디렉토리 생성
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 로거 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                os.path.join(log_dir, "app.log"),
                encoding='utf-8'
            )
        ]
    )

    # uvicorn 로그 레벨 조정 (너무 많은 로그 방지)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return logging.getLogger(__name__)


# 로깅 초기화
logger = setup_logging()

# FastAPI 앱 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="공통 응답 형식을 사용하는 FastAPI 애플리케이션",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# 미들웨어 등록 (순서 중요: 역순으로 실행됨)
def setup_middleware():
    """미들웨어 설정"""

    # CORS 미들웨어 (가장 먼저 실행되어야 함)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(ResponseLogMiddleware)

    logger.info("✅ 미들웨어 설정 완료")


# 라우터 설정
def setup_routers():
    """라우터 설정"""
    # API 라우터 등록
    app.include_router(
        api_router,
        prefix=settings.API_V1_STR,
        tags=["API v1"]
    )

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
            "health": "/health"
        },
        message="API 서버가 정상 작동 중입니다"
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """헬스체크 엔드포인트"""
    return ResponseBuilder.success(
        data={
            "status": "healthy",
            "version": settings.VERSION,
            "environment": "development"  # 환경에 따라 변경
        },
        message="서버 상태 정상"
    )


@app.get("/version", tags=["Info"])
async def get_version():
    """버전 정보"""
    return ResponseBuilder.success(
        data={
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "api_version": "v1"
        },
        message="버전 정보"
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
