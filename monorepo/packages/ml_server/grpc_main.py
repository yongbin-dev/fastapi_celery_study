"""
gRPC ML Server Main Application
AI/ML 모델 추론을 담당하는 gRPC 서버
"""

import sys

from shared.core.logging import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("🚀 gRPC ML 서버 시작 중...")

    try:
        from ml_app.services.grpc_services.server import start_grpc_server

        # gRPC 서버 시작 (블로킹)
        start_grpc_server()

    except KeyboardInterrupt:
        logger.info("🛑 gRPC 서버 종료")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ gRPC 서버 실행 실패: {e}", exc_info=True)
        sys.exit(1)
