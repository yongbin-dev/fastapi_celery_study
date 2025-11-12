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

    logger.info("🚀 ML 서버 시작")

    bentoml_process = None

    # gRPC 서버 시작 (필요시 주석 해제)
    # if USE_GRPC:
    #     from ml_app.grpc_services.server import serve
    #     grpc_task = asyncio.create_task(serve())
    #     logger.info("✅ gRPC 서버 태스크 시작 (포트: 50051)")
    # else:
    #     logger.info("⚠️  gRPC 비활성화 (USE_GRPC=false)")

    # BentoML 서버 시작
    try:
        # 프로세스 생성
        bentoml_process = await asyncio.create_subprocess_exec(
            "bentoml",
            "serve",
            "ml_app.bentoml_services:OCRBentoService",
            "--host",
            "0.0.0.0",
            "--port",
            "50052",
            "--api-workers",
            "1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        logger.info("✅ BentoML 서버 시작됨 (포트: 50052)")

        # 로깅 태스크 시작
        async def log_output(stream, prefix):
            try:
                async for line in stream:
                    logger.info(f"{prefix}: {line.decode().strip()}")
            except Exception:
                pass

        asyncio.create_task(log_output(bentoml_process.stdout, "BentoML"))
        asyncio.create_task(log_output(bentoml_process.stderr, "BentoML-ERR"))

    except Exception as e:
        logger.error(f"❌ BentoML 서버 시작 실패: {e}")

    yield

    # 종료 시
    logger.info("🛑 ML 서버 종료")

    # gRPC 종료 (필요시 주석 해제)
    # if grpc_task:
    #     grpc_task.cancel()
    #     try:
    #         await grpc_task
    #     except asyncio.CancelledError:
    #         logger.info("gRPC 서버 태스크 종료")

    # BentoML 프로세스 종료
    if bentoml_process:
        logger.info("BentoML 서버 종료 중...")
        try:
            # 정상 종료 시도 (SIGTERM)
            bentoml_process.terminate()

            # 5초 대기
            try:
                await asyncio.wait_for(bentoml_process.wait(), timeout=5.0)
                logger.info("✅ BentoML 서버 정상 종료")
            except asyncio.TimeoutError:
                # 타임아웃 시 강제 종료 (SIGKILL)
                logger.warning("BentoML 서버가 응답하지 않음. 강제 종료...")
                bentoml_process.kill()
                await bentoml_process.wait()
                logger.info("✅ BentoML 서버 강제 종료")
        except Exception as e:
            logger.error(f"BentoML 서버 종료 실패: {e}")


app = FastAPI(
    title="ML Model Server",
    version="1.0.0",
    description="AI/ML 모델 추론 서버 - OCR, LLM 등",
    lifespan=lifespan,
)
