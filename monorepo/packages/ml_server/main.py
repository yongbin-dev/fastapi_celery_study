"""
ML Server Main Application
AI/ML 모델 추론을 담당하는 BentoML 서버
"""

import sys

from shared.config import settings
from shared.core.logging import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("🚀 BentoML OCR 서버 시작 중...")

    try:
        import bentoml

        # 서비스 실행 - bentoml serve와 동일하게 동작
        # blocking=True로 설정하여 서버가 종료될 때까지 대기
        bentoml.serve(
            "ml_app.services.bentoml_services:OCRBentoService",
            host=settings.HOST,
            port=settings.ML_SERVER_PORT,
            reload=False,
            working_dir=".",
            blocking=True,  # 서버가 종료될 때까지 블로킹
        )

    except KeyboardInterrupt:
        logger.info("🛑 BentoML 서버 종료")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ BentoML 서버 실행 실패: {e}")
        sys.exit(1)
