"""
Mock OCR 엔진 - 테스트용 가짜 OCR 엔진
"""
from shared.core.logging import get_logger
from shared.schemas import OCRExtractDTO, TextBoxDTO

from .base import BaseOCREngine

logger = get_logger(__name__)


class MockOCREngine(BaseOCREngine):
    """Mock OCR 엔진 - 테스트용"""

    def get_engine_name(self) -> str:
        return "MockOCR"

    def load_model(self) -> None:
        """Mock 모델 로드 (실제로는 아무것도 하지 않음)"""
        try:
            logger.info("MockOCR 모델 로딩 시작...")
            # 실제 모델을 로드하지 않고 즉시 완료
            self.model = "mock_model"
            self.is_loaded = True
            logger.info("MockOCR 모델 로드 완료")
        except Exception as e:
            logger.error(f"MockOCR 모델 로드 중 오류: {e}")
            self.is_loaded = False

    def predict(self, image_data: bytes, confidence_threshold: float) -> OCRExtractDTO:
        """Mock OCR 예측 - 테스트용 가짜 결과 반환"""
        if not self.is_loaded:
            return OCRExtractDTO(
                text_boxes=[], status="failed", error="Model not loaded"
            )

        try:
            logger.info("MockOCR 실행 시작")

            # 테스트용 가짜 텍스트 박스 생성
            mock_text_boxes = [
                TextBoxDTO(
                    text="Mock Text 1",
                    confidence=0.95,
                    bbox=[[10.0, 10.0], [100.0, 10.0], [100.0, 30.0], [10.0, 30.0]],
                ),
                TextBoxDTO(
                    text="Mock Text 2",
                    confidence=0.90,
                    bbox=[[10.0, 40.0], [100.0, 40.0], [100.0, 60.0], [10.0, 60.0]],
                ),
                TextBoxDTO(
                    text="테스트 텍스트",
                    confidence=0.85,
                    bbox=[[10.0, 70.0], [100.0, 70.0], [100.0, 90.0], [10.0, 90.0]],
                ),
            ]

            # confidence_threshold 적용
            filtered_boxes = [
                box for box in mock_text_boxes if box.confidence >= confidence_threshold
            ]

            logger.info(
                f"MockOCR 실행 완료: {len(filtered_boxes)}개 텍스트 박스 반환"
            )

            return OCRExtractDTO(text_boxes=filtered_boxes, status="success")

        except Exception as e:
            logger.error(f"MockOCR predict 실행 중 오류: {str(e)}")
            return OCRExtractDTO(text_boxes=[], status="failed", error=str(e))
