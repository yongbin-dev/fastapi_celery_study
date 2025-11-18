# app/domains/ocr/services/engines/paddleocr_engine.py
from typing import List

import cv2
import numpy as np
from shared.config import settings
from shared.core.logging import get_logger
from shared.schemas import OCRExtractDTO, OCRTextBoxCreate

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
            is_cuda_available = paddle.device.is_compiled_with_cuda()
            logger.info(f"CUDA 지원 여부: {is_cuda_available}")

            if is_cuda_available:
                logger.info(f"현재 디바이스: {paddle.get_device()}")
                logger.info(f"GPU 개수: {paddle.device.cuda.device_count()}")

        except ImportError as e:
            logger.error(f"PaddleOCR 또는 Paddle 모듈을 불러올 수 없습니다: {e}")
            self.is_loaded = False
            return

        try:
            logger.info("PaddleOCR 모델 로딩 시작...")

            # GPU 사용 가능 여부 확인 (macOS에서는 False)
            import platform
            use_gpu = is_cuda_available and platform.system() != "Darwin"

            logger.info(f"플랫폼: {platform.system()}, GPU 사용: {use_gpu}")

            ocr_params = {
                "use_angle_cls": self.use_angle_cls,
                "lang": "korean" if self.lang == "korean" else "en",
                "det_model_dir": settings.OCR_DET,
                "rec_model_dir": settings.OCR_REC,
                "use_gpu": use_gpu,
                "show_log": True,  # PaddleOCR 내부 로그 활성화
            }

            logger.info(f"PaddleOCR 초기화 파라미터: {ocr_params}")
            logger.info("PaddleOCR 객체 생성 중...")

            self.model = PaddleOCR(**ocr_params)

            logger.info("PaddleOCR 객체 생성 완료")
            self.is_loaded = True
            logger.info(f"✅ PaddleOCR 모델 로드 완료 (lang={ocr_params['lang']}, gpu={use_gpu})")

        except Exception as e:
            logger.error(f"❌ PaddleOCR 모델 로드 중 오류: {e}", exc_info=True)
            self.is_loaded = False

    def predict(self, image_data: bytes, confidence_threshold: float) -> OCRExtractDTO:
        """PaddleOCR 예측"""
        if not self.is_loaded or self.model is None:
            return OCRExtractDTO(
                text_boxes=[], status="failed", error="Model not loaded"
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
                            OCRTextBoxCreate(
                                text=text,
                                confidence=float(confidence),
                                bbox=bbox_list,
                            )
                        )

            logger.info(f"PaddleOCR 실행 완료: {len(text_boxes)}개 텍스트 검출")

            return OCRExtractDTO(text_boxes=text_boxes, status="success")

        except Exception as e:
            logger.error(f"PaddleOCR predict 실행 중 오류: {str(e)}")
            return OCRExtractDTO(text_boxes=[], status="failed", error=str(e))

    def predict_batch(
        self, image_data_list: List[bytes], confidence_threshold: float
    ) -> List[OCRExtractDTO]:
        if not self.is_loaded or self.model is None:
            return [
                OCRExtractDTO(text_boxes=[], status="failed", error="Model not loaded")
            ]

        result = self.model.ocr(image_data_list)
        return result
