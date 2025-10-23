# pipeline_tasks.py
"""
파이프라인 Celery 태스크
celery_worker에서만 정의되고 실행됨
"""

import asyncio

from celery_app import celery_app
from ml_app.models.ocr_model import get_ocr_model
from shared.core.logging import get_logger
from shared.utils.file_utils import load_uploaded_image

logger = get_logger(__name__)


@celery_app.task(bind=True, name="tasks.ocr_extract")
def ocr_extract_task(
    self,
    chain_id: str,
    image_path: str,
    language: str = "korean",
    confidence_threshold: float = 0.5,
    use_angle_cls: bool = True,
):
    """
    OCR 텍스트 추출 태스크

    Args:
        image_path: 이미지 경로
        language: 언어 (korean, english 등)
        confidence_threshold: 신뢰도 임계값
        use_angle_cls: 각도 분류 사용 여부

    Returns:
        OCR 추출 결과
    """
    logger.info(f"🚀 OCR 추출 태스크 시작: chain_id : {chain_id} path : {image_path}")
    image_data: bytes = asyncio.run(load_uploaded_image(image_path))
    ocr_model = get_ocr_model(use_angle_cls=use_angle_cls, lang=language)

    # OCR 실행
    ocr_result = ocr_model.predict(image_data, confidence_threshold)

    logger.info(f"✅ OCR 추출 태스크 완료: {image_path}")
    return ocr_result
