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

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """LLM 입력 데이터 검증"""
        if "prompt" not in input_data and "message" not in input_data:
            return False
        return True

    def preprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """전처리: 프롬프트 정제"""
        if "prompt" in input_data:
            input_data["prompt"] = input_data["prompt"].strip()
        if "message" in input_data:
            input_data["message"] = input_data["message"].strip()
        return input_data



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
        
        # 모델 로드 (싱글톤)
        if self.model is None:
            self.model = get_ocr_model(use_angle_cls=use_angle_cls, lang=language)

        # OCR 실행
        logger.info(f"OCR 실행 시작: 이미지 크기 {len(image_data)} bytes")
        result = self.model.predict(image_data, confidence_threshold)

        # 후처리
        result = self.postprocess(result)

        logger.info(f"OCR 실행 완료")
        return result



ocr_service = OCRService()


def get_ocr_service() :
    return ocr_service
