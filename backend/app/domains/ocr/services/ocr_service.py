# app/domains/ocr/services/ocr_service.py
from typing import Optional

from app.core.logging import get_logger
from app.shared.base_service import BaseService

from ..schemas import OCRResultDTO
from .ocr_model import OCRModel, get_ocr_model

logger = get_logger(__name__)


class OCRService(BaseService):
    """OCR 비즈니스 로직 서비스"""

    def __init__(self):
        super().__init__()
        self.model: Optional[OCRModel] = None

    def extract_text_from_image(
        self,
        image_data: bytes,
        language: str = "korean",
        confidence_threshold: float = 0.5,
        use_angle_cls: bool = True,
    ) -> OCRResultDTO:
        """
        OCR 텍스트 추출 메인 메서드

        Args:
            image_data: 이미지 데이터 (bytes)
            filename: 원본 파일명
            language: 추출할 언어
            confidence_threshold: 신뢰도 임계값
            use_angle_cls: 각도 분류 사용 여부
            chain_id: Celery chain ID (선택적)

        Returns:
            OCRResultDTO: 추출된 텍스트 결과
        """

        if self.model is None:
            self.model = get_ocr_model(use_angle_cls=use_angle_cls, lang=language)

        logger.info(f"OCR 실행 시작: 이미지 크기 {len(image_data)} bytes")
        result = self.model.predict(image_data, confidence_threshold)

        logger.info("OCR 실행 완료")
        return result


ocr_service = OCRService()


def get_ocr_service():
    return ocr_service
