"""
ML Server Main Application
AI/ML 모델 추론을 담당하는 BentoML 서버
"""

import sys
import threading

from shared.config import settings
from shared.core.logging import get_logger

logger = get_logger(__name__)


def load_model_in_background():
    """백그라운드에서 OCR 모델 로드"""
    try:
        from ml_app.models.ocr_model import get_ocr_model

        logger.info("📦 백그라운드에서 OCR 모델 로드 시작...")
        ocr_model = get_ocr_model()

        if ocr_model.is_loaded:
            logger.info("✅ OCR 모델 로드 완료")
        else:
            logger.warning(
                "⚠️ OCR 모델 로드 실패 - "
                "요청 처리가 실패할 수 있습니다"
            )
    except Exception as e:
        logger.error(f"❌ OCR 모델 로드 중 오류: {e}", exc_info=True)
        logger.warning("⚠️ 요청 처리가 실패할 수 있습니다")


if __name__ == "__main__":
    logger.info("🚀 BentoML OCR 서버 시작 중...")

    try:
        import bentoml

        # 백그라운드 스레드에서 모델 로드 시작
        logger.info("🔄 백그라운드에서 모델 로드를 시작합니다...")
        model_loader_thread = threading.Thread(
            target=load_model_in_background, daemon=True
        )
        model_loader_thread.start()

        # 서버는 즉시 시작 (모델 로드 완료를 기다리지 않음)
        server_url = f"http://{settings.HOST}:{settings.ML_SERVER_PORT}"
        logger.info(f"🌐 서버 시작: {server_url}")
        logger.info(
            "💡 모델은 백그라운드에서 로드됩니다. "
            "/health_check로 상태를 확인하세요."
        )

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
