# app/domains/ocr/services/engines/paddleocr_engine.py
import traceback

from app.config import settings
from app.core.logging import get_logger

from ...schemas import OCRResultDTO, TextBoxDTO
from .base import BaseOCREngine

logger = get_logger(__name__)


class PaddleOCREngine(BaseOCREngine):
    """PaddleOCR 엔진"""

    def get_engine_name(self) -> str:
        return "PaddleOCR"

    def load_model(self) -> None:
        """PaddleOCR 모델 로드"""

        try:
            import paddle
            from paddleocr import PaddleOCR
        except ImportError:
            PaddleOCR = None

        print(
            "CUDA 지원 여부:", paddle.device.is_compiled_with_cuda()
        )  # True 여야 GPU 빌드
        print("현재 디바이스:", paddle.get_device())  # gpu:0 기대
        print("GPU 개수:", paddle.device.cuda.device_count())  # 1 이상이어야 함

        if PaddleOCR is None:
            logger.error("PaddleOCR 모듈이 설치되지 않았습니다.")
            self.is_loaded = False
            return

        try:
            ocr_params = {
                "use_angle_cls": True,
                "lang": "en",  # 다국어 모델 사용
                "det_model_dir": settings.OCR_DET,
                "rec_model_dir": settings.OCR_REC,
            }
            self.model = PaddleOCR(**ocr_params)
            self.is_loaded = True

        except Exception as e:
            logger.error(f"Error loading PaddleOCR model: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.is_loaded = False

    def predict(self, image_data: bytes, confidence_threshold: float) -> OCRResultDTO:
        """PaddleOCR 예측"""
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        if not self.is_loaded or self.model is None:
            return OCRResultDTO(
                text_boxes=[], full_text="", status="failed", error="Model not loaded"
            )

        try:
            logger.info("PaddleOCR 실행 시작")

            # 바이트를 numpy 배열로 변환
            nparr = np.frombuffer(image_data, np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # PaddleOCR 실행
            result = self.model.ocr(img_np)

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
                            TextBoxDTO(
                                text=text,
                                confidence=float(confidence),
                                bbox=bbox_list,
                            )
                        )

            full_text = " ".join([box.text for box in text_boxes])

            logger.info(f"PaddleOCR 실행 완료: {len(text_boxes)}개 텍스트 검출")

            return OCRResultDTO(
                text_boxes=text_boxes, full_text=full_text, status="success"
            )

        except Exception as e:
            logger.error(f"PaddleOCR predict 실행 중 오류: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return OCRResultDTO(
                text_boxes=[], full_text="", status="failed", error=str(e)
            )
