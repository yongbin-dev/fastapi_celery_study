# packages/ml_server/ml_app/grpc_services/server.py
"""gRPC 서버 관리"""

import asyncio

import grpc
from shared.config import settings
from shared.core.logging import get_logger
from shared.grpc.generated import ocr_pb2_grpc

from .ocr_service import OCRServiceServicer

logger = get_logger(__name__)


async def serve():
    """gRPC 서버 시작"""

    # 0. OCR 모델 미리 로드
    logger.info("📦 OCR 모델 미리 로드 시작...")
    from ml_app.models.ocr_model import get_ocr_model

    try:
        ocr_model = get_ocr_model()
        if ocr_model.is_loaded:
            logger.info("✅ OCR 모델 미리 로드 완료")
        else:
            logger.warning(
                "⚠️ OCR 모델 로드 실패 - 서비스는 시작되지만 "
                "요청 처리가 실패할 수 있습니다"
            )
    except Exception as e:
        logger.error(f"❌ OCR 모델 미리 로드 중 오류: {e}", exc_info=True)
        logger.warning("⚠️ 서비스는 시작되지만 요청 처리가 실패할 수 있습니다")

    # 1. 서버 생성
    server = grpc.aio.server(
        options=[
            ("grpc.max_send_message_length", 100 * 1024 * 1024),  # 100MB
            ("grpc.max_receive_message_length", 100 * 1024 * 1024),
            ("grpc.keepalive_time_ms", 10000),
            ("grpc.keepalive_timeout_ms", 5000),
        ]
    )
    # 2. 서비스 등록
    ocr_pb2_grpc.add_OCRServiceServicer_to_server(OCRServiceServicer(), server)

    # 3. 포트 바인딩
    grpc_port = settings.GRPC_PORT
    server.add_insecure_port(f"[::]:{grpc_port}")

    # 4. 서버 시작
    await server.start()
    logger.info(f"🚀 gRPC 서버 시작 완료: 포트 {grpc_port}")

    # 5. 종료 대기
    await server.wait_for_termination()


def start_grpc_server():
    """gRPC 서버 시작 (블로킹)"""
    asyncio.run(serve())


if __name__ == "__main__":
    start_grpc_server()
