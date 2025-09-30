# app/domains/ocr/services/engines/paddleocr_engine.py
from typing import Dict, Any
from .base import BaseOCREngine
from app.core.logging import get_logger
import traceback
import cv2
import numpy as np
from app.config import settings

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
            logger.info("rect_model_dir: " + settings.OCR_REC)
            logger.info("dect_model_dir: " + settings.OCR_DET)
            # PaddleOCR 생성
            self.model = PaddleOCR(
                # text_detection_model_name=settings.OCR_DET,
                # text_recognition_model_name=settings.OCR_REC,
                # device="gpu",
                # use_doc_orientation_classify=False, # 通过 use_doc_orientation_classify 参数指定不使用文档方向分类模型
                # use_doc_unwarping=False, # 通过 use_doc_unwarping 参数指定不使用文本图像矫正模型
                # use_textline_orientation=False, # 通过 use_textline_orientation 参数指定不使用文本行方向分类模型

                # text_recognition_model_dir=settings.OCR_REC,
                # text_detection_model_dir=settings.OCR_DET,
                # use_angle_cls=False, # 필요에 따라 설정
                # use_cuda=True # GPU 사용 여부
                # use_angle_cls=self.use_angle_cls,
                # lang=self.lang,
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
            result = self.model.ocr(img_np)

            return result
            # 결과 파싱
            # text_boxes = []
            # if result and result[0]:
            #     for line in result[0]:
            #         bbox = line[0]
            #         text = line[1][0]
            #         confidence = line[1][1]

            #         if confidence >= confidence_threshold:
            #             # numpy 배열을 Python 리스트로 변환
            #             bbox_list = [[float(x), float(y)] for x, y in bbox]
            #             text_boxes.append(
            #                 {
            #                     "text": text,
            #                     "confidence": float(confidence),
            #                     "bbox": bbox_list,
            #                 }
            #             )

            # full_text = " ".join([box["text"] for box in text_boxes])

            # logger.info(f"PaddleOCR 실행 완료: {len(text_boxes)}개 텍스트 검출")

            # return {
            #     "text_boxes": text_boxes,
            #     "full_text": full_text,
            #     "status": "success",
            # }

        except Exception as e:
            logger.error(f"PaddleOCR predict 실행 중 오류: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e), "status": "failed"}
