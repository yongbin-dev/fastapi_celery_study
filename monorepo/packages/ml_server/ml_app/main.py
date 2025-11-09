"""
ML Server Main Application
AI/ML 모델 추론을 담당하는 서버
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.config import settings
from shared.core.auto_router import setup_auto_routers
from shared.core.logging import get_logger
from shared.middleware.request_middleware import RequestLogMiddleware
from shared.middleware.response_middleware import ResponseLogMiddleware

logger = get_logger(__name__)

# gRPC 활성화 여부
USE_GRPC = settings.USE_GRPC == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""

    # 시작 시
    logger.info("🚀 ML 서버 시작")

    # OCR 모델 사전 로딩
    try:
        from ml_app.models.ocr_model import get_ocr_model
        logger.info("📦 OCR 모델 로딩 시작...")

        # settings에서 기본값 가져오기
        ocr_model = get_ocr_model(
            use_angle_cls=settings.OCR_USE_ANGLE_CLS,
            lang=settings.OCR_LANG
        )

        if ocr_model.is_loaded:
            logger.info(
                f"✅ OCR 모델 로딩 완료 - "
                f"엔진: {settings.OCR_ENGINE}, "
                f"언어: {settings.OCR_LANG}, "
                f"각도보정: {settings.OCR_USE_ANGLE_CLS}"
            )
        else:
            logger.warning("⚠️  OCR 모델 로딩 실패")
    except Exception as e:
        logger.error(f"❌ OCR 모델 로딩 중 에러 발생: {str(e)}", exc_info=True)

    grpc_task = None
    if USE_GRPC:
        # gRPC 서버를 별도 태스크로 시작
        from ml_app.grpc_services.server import serve
        grpc_task = asyncio.create_task(serve())
        logger.info("✅ gRPC 서버 태스크 시작")
    else:
        logger.info("⚠️  gRPC 비활성화 (USE_GRPC=false)")

    yield

    # 종료 시
    logger.info("🛑 ML 서버 종료")
    if grpc_task:
        grpc_task.cancel()
        try:
            await grpc_task
        except asyncio.CancelledError:
            logger.info("gRPC 서버 태스크 종료")


app = FastAPI(
    title="ML Model Server",
    version="1.0.0",
    description="AI/ML 모델 추론 서버 - OCR, LLM 등",
    lifespan=lifespan
)


# 라우터 설정
def setup_routers():
    """라우터 설정 - 자동 스캔 및 등록"""
    import pathlib

    current_dir = pathlib.Path(__file__).parent
    domains_path = str(current_dir / "domains")

    app.add_middleware(ResponseLogMiddleware)
    app.add_middleware(RequestLogMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("✅ 미들웨어 설정 완료")

    auto_router = setup_auto_routers(
        app=app,
        domains_path=domains_path,
        exclude_domains=[],
        global_prefix="/api/model",
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


setup_routers()


@app.get("/")
async def root():
    return {
        "service": "ML Model Server",
        "version": "1.0.0",
        "models": ["ocr"],
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ml_server"}
