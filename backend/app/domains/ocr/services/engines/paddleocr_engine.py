# app/domains/ocr/services/engines/paddleocr_engine.py
from typing import Dict, Any
from .base import BaseOCREngine
from app.core.logging import get_logger
import traceback
import cv2
import numpy as np

logger = get_logger(__name__)


class PaddleOCREngine(BaseOCREngine):
    """PaddleOCR 엔진"""

    def get_engine_name(self) -> str:
        return "PaddleOCR"

    def load_model(self) -> None:
        """PaddleOCR 모델 로드"""
        try:
            from paddleocr import PaddleOCR

            logger.info("PaddleOCR 모델 로딩 시작...")

            # PaddleOCR 생성
            self.model = PaddleOCR(
                use_angle_cls=self.use_angle_cls,
                lang=self.lang,
            )

            logger.info(f"PaddleOCR Model loaded (lang={self.lang})")
            self.is_loaded = True

        except Exception as e:
            logger.error(f"Error loading PaddleOCR model: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.is_loaded = False

    def predict(self, image_data: bytes, confidence_threshold: float) -> Dict[str, Any]:
        """PaddleOCR 예측"""
        if not self.is_loaded or self.model is None:
            return {"error": "Model not loaded", "status": "failed"}

        try:
            logger.info(f"PaddleOCR 실행 시작")

            # 바이트를 numpy 배열로 변환
            nparr = np.frombuffer(image_data, np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # PaddleOCR 실행
            result = self.model.ocr(img_np, cls=self.use_angle_cls)

            # 결과 파싱
            text_boxes = []
            if result and result[0]:
                for line in result[0]:
                    bbox = line[0]
                    text = line[1][0]
                    confidence = line[1][1]

                    if confidence >= confidence_threshold:
                        # numpy 배열을 Python 리스트로 변환
                        bbox_list = [[float(x), float(y)] for x, y in bbox]
                        text_boxes.append(
                            {
                                "text": text,
                                "confidence": float(confidence),
                                "bbox": bbox_list,
                            }
                        )

            full_text = " ".join([box["text"] for box in text_boxes])

            logger.info(f"PaddleOCR 실행 완료: {len(text_boxes)}개 텍스트 검출")

            return {
                "text_boxes": text_boxes,
                "full_text": full_text,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"PaddleOCR predict 실행 중 오류: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e), "status": "failed"}