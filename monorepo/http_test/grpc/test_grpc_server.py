#!/usr/bin/env python3
"""독립 gRPC 서버"""

import sys
import asyncio
from pathlib import Path

# 경로 추가
root = Path(__file__).parent
sys.path.insert(0, str(root / "packages" / "shared"))
sys.path.insert(0, str(root / "packages" / "ml_server"))

import grpc
from shared.config import settings
from shared.core.logging import get_logger
from shared.grpc.generated import ocr_pb2_grpc

logger = get_logger(__name__)

async def serve():
    """gRPC 서버 시작"""
    # OCRServiceServicer를 여기서 import
    from ml_app.grpc_services.ocr_service import OCRServiceServicer

    # 1. 서버 생성
    server = grpc.aio.server(
        options=[
            ('grpc.max_send_message_length', 100 * 1024 * 1024),
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
    logger.info(f"🚀 gRPC 서버 시작 중: 포트 {grpc_port}")
    server.add_insecure_port(f'[::]:{grpc_port}')

    # 4. 서버 시작
    await server.start()
    logger.info(f"✅ gRPC 서버 준비 완료: 포트 {grpc_port}")

    # 5. 종료 대기
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("gRPC 서버 종료 중...")
        await server.stop(grace=5)

if __name__ == "__main__":
    print("🚀 독립 gRPC 서버 시작...")
    asyncio.run(serve())
