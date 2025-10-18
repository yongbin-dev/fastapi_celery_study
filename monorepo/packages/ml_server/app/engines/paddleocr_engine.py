# app/domains/ocr/services/engines/paddleocr_engine.py
import cv2  # type: ignore
import numpy as np  # type: ignore
from shared.config import settings
from shared.core.logging import get_logger
from shared.schemas import OCRExtractDTO, TextBoxDTO

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

            # GPU 환경 정보 로깅
            logger.debug(f"CUDA 지원 여부: {paddle.device.is_compiled_with_cuda()}")
            logger.debug(f"현재 디바이스: {paddle.get_device()}")
            logger.debug(f"GPU 개수: {paddle.device.cuda.device_count()}")

        except ImportError as e:
            logger.error(f"PaddleOCR 또는 Paddle 모듈을 불러올 수 없습니다: {e}")
            self.is_loaded = False
            return

        try:
            logger.info("PaddleOCR 모델 로딩 시작...")

            ocr_params = {
                "use_angle_cls": self.use_angle_cls,
                "lang": "korean" if self.lang == "korean" else "en",
                "det_model_dir": settings.OCR_DET,
                "rec_model_dir": settings.OCR_REC,
                "use_gpu": True,
                "show_log": False,
            }

            self.model = PaddleOCR(**ocr_params)
            self.is_loaded = True
            logger.info(f"PaddleOCR 모델 로드 완료 (lang={ocr_params['lang']})")

        except Exception as e:
            logger.error(f"PaddleOCR 모델 로드 중 오류: {e}")
            self.is_loaded = False

    def predict(self, image_data: bytes, confidence_threshold: float) -> OCRExtractDTO:
        """PaddleOCR 예측"""
        if not self.is_loaded or self.model is None:
            return OCRExtractDTO(
                text_boxes=[],  status="failed", error="Model not loaded"
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


            logger.info(f"PaddleOCR 실행 완료: {len(text_boxes)}개 텍스트 검출")

            return OCRExtractDTO(
                text_boxes=text_boxes,  status="success"
            )

        except Exception as e:
            logger.error(f"PaddleOCR predict 실행 중 오류: {str(e)}")
            return OCRExtractDTO(
                text_boxes=[], status="failed", error=str(e)
            )
