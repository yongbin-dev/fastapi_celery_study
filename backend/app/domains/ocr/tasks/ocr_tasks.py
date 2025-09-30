# app/domains/ocr/tasks/ocr_tasks.py
from typing import Dict, Any
from app.celery_app import celery_app
from app.core.logging import get_logger
from ..services.ocr_model import OCRModel
from ..services.ocr_service import OCRService

logger = get_logger(__name__)


@celery_app.task(bind=True, name="ocr.extract_text")
def extract_text_task(
    self, image_path: str, language: str = "korean", confidence_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    OCR 텍스트 추출 태스크

    Args:
        image_path: 이미지 파일 경로
        language: 추출할 언어
        confidence_threshold: 신뢰도 임계값

    Returns:
        추출된 텍스트 결과
    """
    logger.info(f"OCR 텍스트 추출 시작 - Task ID: {self.request.id}, Image: {image_path}")

    try:
        # 입력 데이터 검증
        service = OCRService()
        input_data = {"image_path": image_path, "confidence_threshold": confidence_threshold}

        if not service.validate_input(input_data):
            logger.error(f"OCR 입력 데이터 검증 실패 - Task ID: {self.request.id}")
            return {"error": "Invalid input data", "status": "failed"}

        # 전처리
        input_data = service.preprocess(input_data)

        # OCR 모델 로드 및 실행
        model = OCRModel(use_angle_cls=True, lang=language)
        model.load_model()

        result = model.predict(input_data)

        logger.info(f"OCR 텍스트 추출 완료 - Task ID: {self.request.id}")
        return result

    except Exception as e:
        logger.error(f"OCR 텍스트 추출 실패 - Task ID: {self.request.id}, Error: {str(e)}")
        return {"error": str(e), "status": "failed"}