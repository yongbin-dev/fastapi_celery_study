# app/domains/ocr/services/ocr_service.py
from app.shared.base_service import BaseService
from typing import Dict, Any, Optional
from .ocr_model import get_ocr_model, OCRModel
from app.core.logging import get_logger

logger = get_logger(__name__)


class OCRService(BaseService):
    """OCR 비즈니스 로직 서비스"""

    def __init__(self):
        super().__init__()
        self.model: Optional[OCRModel] = None

    def postprocess(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """후처리: 결과 데이터 정제"""
        if result.get("status") == "failed":
            return result

        # 텍스트 박스 정보 정리
        if "text_boxes" in result:
            result["total_boxes"] = len(result["text_boxes"])
            result["average_confidence"] = (
                sum(box.get("confidence", 0) for box in result["text_boxes"])
                / len(result["text_boxes"])
                if result["text_boxes"]
                else 0
            )

        return result

    def extract_text_from_image(
        self,
        image_data: bytes,
        language: str = "korean",
        confidence_threshold: float = 0.5,
        use_angle_cls: bool = True,
    ) -> Dict[str, Any]:
        """
        OCR 텍스트 추출 메인 메서드

        Args:
            image_data: 이미지 데이터 (bytes)
            language: 추출할 언어
            confidence_threshold: 신뢰도 임계값
            use_angle_cls: 각도 분류 사용 여부

        Returns:
            추출된 텍스트 결과
        """
        try:
            # 모델 로드 (싱글톤)
            if self.model is None:
                self.model = get_ocr_model(use_angle_cls=use_angle_cls, lang=language)

            # OCR 실행
            logger.info(f"OCR 실행 시작: 이미지 크기 {len(image_data)} bytes")
            result = self.model.predict(image_data, confidence_threshold)

            # 후처리
            result = self.postprocess(result)

            logger.info(f"OCR 실행 완료")
            return 

        except Exception as e:
            logger.error(f"OCR 실행 중 오류 발생: {str(e)}")
            return {"error": str(e), "status": "failed"}


ocr_service = OCRService()


def get_ocr_service() :
    return ocr_service
