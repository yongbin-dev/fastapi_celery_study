# app/domains/ocr/services/engines/mock_engine.py
from typing import Dict, Any
from .base import BaseOCREngine
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockOCREngine(BaseOCREngine):
    """Mock OCR 엔진 (테스트용)"""

    def get_engine_name(self) -> str:
        return "MockOCR"

    def load_model(self) -> None:
        """Mock 모델 로드 (실제로는 아무것도 하지 않음)"""
        logger.info("Mock OCR 모드 활성화")
        self.model = None
        self.is_loaded = True

    def predict(self, image_data: bytes, confidence_threshold: float) -> Dict[str, Any]:
        """Mock OCR 예측 (샘플 데이터 반환)"""
        if not self.is_loaded:
            return {"error": "Model not loaded", "status": "failed"}

        logger.info(f"Mock OCR 실행: 이미지 데이터 (size: {len(image_data)} bytes)")

        text_boxes = [
            {
                "text": "Controller → Service → Model 구조 테스트",
                "confidence": 0.98,
                "bbox": [[10.0, 10.0], [400.0, 10.0], [400.0, 50.0], [10.0, 50.0]],
            },
            {
                "text": "이미지 바이트 데이터가 정상적으로 수신되었습니다",
                "confidence": 0.95,
                "bbox": [[10.0, 60.0], [350.0, 60.0], [350.0, 90.0], [10.0, 90.0]],
            },
            {
                "text": "Mock OCR 응답이 정상적으로 반환되었습니다",
                "confidence": 0.92,
                "bbox": [[10.0, 100.0], [380.0, 100.0], [380.0, 130.0], [10.0, 130.0]],
            },
        ]

        full_text = " ".join([box["text"] for box in text_boxes])

        logger.info(f"Mock OCR 실행 완료: {len(text_boxes)}개 텍스트 검출")

        return {
            "text_boxes": text_boxes,
            "full_text": full_text,
            "status": "success",
        }