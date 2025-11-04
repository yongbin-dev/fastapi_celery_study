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

    # 1. 서버 생성
    server = grpc.aio.server(
        options=[
            ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
        ]
    )
    # 2. 서비스 등록
    ocr_pb2_grpc.add_OCRServiceServicer_to_server(
        OCRServiceServicer(),
        server
    )

    # 3. 포트 바인딩
    grpc_port = settings.GRPC_PORT
    logger.info(f"🚀 gRPC 서버 시작: 포트 {grpc_port}")
    server.add_insecure_port(f'[::]:{grpc_port}')

    # 4. 서버 시작
    await server.start()
    logger.info(f"🚀 gRPC 서버 시작: 포트 {grpc_port}")

    # 5. 종료 대기
    await server.wait_for_termination()


def start_grpc_server():
    """gRPC 서버 시작 (블로킹)"""
    asyncio.run(serve())
