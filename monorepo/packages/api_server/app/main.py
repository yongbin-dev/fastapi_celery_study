# app/main.py (개선 버전)

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.config import settings
from shared.core import get_logger
from shared.core.auto_router import setup_auto_routers
from shared.core.database import close_db, init_db
from shared.handler.exceptions_handler import (
    general_exception_handler,
)
from shared.middleware.request_middleware import RequestLogMiddleware
from shared.middleware.response_middleware import ResponseLogMiddleware
from shared.utils.response_builder import ResponseBuilder

logger = get_logger(__name__)


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
    logger.info(f"📋 설정: {settings.PROJECT_NAME} v{settings.VERSION}")

    await init_db()
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
from shared.core.logging import get_logger  # noqa: E402

logger = get_logger(__name__)

# FastAPI 앱 생성 (exception handlers 미리 등록)
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="공통 응답 형식을 사용하는 FastAPI 애플리케이션",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    exception_handlers={
        Exception: general_exception_handler,
    },
)


# 미들웨어 등록 (순서 중요: 역순으로 실행됨)
def setup_middleware():
    """미들웨어 설정"""

    # 로깅 미들웨어 활성화
    app.add_middleware(ResponseLogMiddleware)
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
    """라우터 설정 - 자동 스캔 및 등록"""
    # 현재 파일의 디렉토리 기준으로 domains 경로 계산
    import pathlib

    current_dir = pathlib.Path(__file__).parent
    domains_path = str(current_dir / "domains")

    # domains 내의 모든 controller를 자동으로 검색하고 등록
    auto_router = setup_auto_routers(
        app=app,
        domains_path=domains_path,
        exclude_domains=[],  # 제외할 도메인이 있으면 여기에 추가
        global_prefix="/api/v1",
    )

    # 등록된 router 정보 로깅
    registered = auto_router.get_registered_routers()
    logger.info(f"✅ 라우터 설정 완료 - 등록된 routers: {len(registered)}개")
    for router_info in registered:
        logger.info(
            f"  - {router_info['module']} "
            f"(prefix: {router_info['prefix']}, "
            f"tags: {router_info['tags']})"
        )


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
async def health_check2():
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


@app.get("/test-error", tags=["Test"])
async def test_error():
    """Global Exception Handler 테스트"""
    raise Exception("테스트 에러: Global handler가 이 에러를 처리합니다")


# 애플리케이션 설정 초기화
def create_application() -> FastAPI:
    """애플리케이션 생성 및 설정"""
    setup_middleware()
    setup_routers()
    logger.info("🎉 FastAPI 애플리케이션 설정 완료")
    return app


# 애플리케이션 초기화 실행
create_application()
