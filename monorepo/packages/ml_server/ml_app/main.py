"""
ML Server Main Application
AI/ML 모델 추론을 담당하는 서버
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from shared.config import settings
from shared.core.logging import get_logger

logger = get_logger(__name__)

# gRPC 활성화 여부
USE_GRPC = settings.USE_GRPC == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""

    # 시작 시

    # 시작 시
    logger.info("🚀 ML 서버 시작")

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
    lifespan=lifespan,
)
