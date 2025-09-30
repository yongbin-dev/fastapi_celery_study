# app/domains/ocr/services/ocr_model.py
from app.shared.base_model import BaseModel
from typing import Dict, Any


class OCRModel(BaseModel):
    """OCR 모델 클래스 (PaddleOCR 사용)"""

    def __init__(self, use_angle_cls: bool = True, lang: str = "korean"):
        super().__init__()
        self.use_angle_cls = use_angle_cls
        self.lang = lang

    def load_model(self):
        """모델 로드"""
        try:
            # PaddleOCR import (실제 사용 시 활성화)
            # from paddleocr import PaddleOCR
            # self.model = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.lang)

            # 개발 환경을 위한 임시 구현
            print(f"OCR Model loaded (use_angle_cls={self.use_angle_cls}, lang={self.lang})")
            self.model = "OCR_MODEL_PLACEHOLDER"  # 실제로는 PaddleOCR 인스턴스
            self.is_loaded = True

        except Exception as e:
            print(f"Error loading OCR model: {e}")
            self.is_loaded = False

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """OCR 텍스트 추출 실행"""
        if not self.is_loaded:
            return {"error": "Model not loaded", "status": "failed"}

        image_path = input_data.get("image_path", "")
        confidence_threshold = input_data.get("confidence_threshold", 0.5)

        try:
            # 실제 OCR 실행 (paddleocr 설치 시 활성화)
            # result = self.model.ocr(image_path, cls=self.use_angle_cls)

            # 개발 환경을 위한 임시 응답
            result = [
                {
                    "text": "샘플 텍스트",
                    "confidence": 0.95,
                    "bbox": [[10, 10], [100, 10], [100, 50], [10, 50]]
                }
            ]

            # 신뢰도 필터링
            filtered_results = [
                box for box in result
                if box.get("confidence", 0) >= confidence_threshold
            ]

            full_text = " ".join([box["text"] for box in filtered_results])

            return {
                "text_boxes": filtered_results,
                "full_text": full_text,
                "status": "success"
            }

        except Exception as e:
            return {"error": str(e), "status": "failed"}