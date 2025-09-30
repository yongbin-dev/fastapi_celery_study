# app/domains/ocr/tasks/ocr_tasks.py
from app.celery_app import celery_app
from app.core.logging import get_logger
from domains.ocr.schemas.response import OCRResultDTO
from ..services.ocr_service import get_ocr_service

logger = get_logger(__name__)


@celery_app.task(bind=True, name="ocr.extract_text")
def extract_text_task(
    self,
    image_data: bytes,
    language: str = "korean",
    confidence_threshold: float = 0.5,
    use_angle_cls: bool = True,
) -> OCRResultDTO:
    """
    OCR 텍스트 추출 태스크

    Args:
        image_data: 이미지 데이터 (bytes)
        language: 추출할 언어
        confidence_threshold: 신뢰도 임계값
        use_angle_cls: 각도 분류 사용 여부

    Returns:
        추출된 텍스트 결과
    """
    logger.info(
        f"OCR 텍스트 추출 시작 - Task ID: {self.request.id}, Image Size: {len(image_data)} bytes"
    )

    # Service를 통한 OCR 실행
    service = get_ocr_service()
    result = service.extract_text_from_image(
        image_data=image_data,
        language=language,
        confidence_threshold=confidence_threshold,
        use_angle_cls=use_angle_cls,
    )

    logger.info(f"OCR 텍스트 추출 완료 - Task ID: {self.request.id}")
    return result
