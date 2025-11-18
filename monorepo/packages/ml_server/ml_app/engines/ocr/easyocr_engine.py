# app/domains/ocr/services/engines/easyocr_engine.py
from typing import List

from shared.core.logging import get_logger
from shared.schemas import OCRExtractDTO, OCRTextBoxCreate

from .base import BaseOCREngine

logger = get_logger(__name__)


class EasyOCREngine(BaseOCREngine):
    """EasyOCR 엔진"""

    def get_engine_name(self) -> str:
        return "EasyOCR"

    def load_model(self) -> None:
        """EasyOCR 모델 로드"""
        try:
            import easyocr

            logger.info("EasyOCR 모델 로딩 시작...")

            # EasyOCR 언어 코드 매핑 (확장 가능)
            lang_map = {
                "korean": "ko",
                "english": "en",
                "chinese": "ch_sim",
                "chinese_traditional": "ch_tra",
                "japanese": "ja",
                "thai": "th",
                "vietnamese": "vi",
                "arabic": "ar",
                "hindi": "hi",
                "spanish": "es",
                "french": "fr",
                "german": "de",
                "russian": "ru",
                "portuguese": "pt",
            }
            lang_code = lang_map.get(self.lang.lower(), "en")

            # 다중 언어 설정 (기본 언어 + 영어)
            languages = [lang_code]
            if lang_code != "en":
                languages.append("en")

            # EasyOCR Reader 생성
            self.model = easyocr.Reader(languages)

            logger.info(f"EasyOCR 모델 로드 완료 (lang={'+'.join(languages)})")
            self.is_loaded = True

        except Exception as e:
            logger.error(f"EasyOCR 모델 로드 중 오류: {e}")
            self.is_loaded = False

    def predict(self, image_data: bytes, confidence_threshold: float) -> OCRExtractDTO:
        """EasyOCR 예측"""
        if not self.is_loaded or self.model is None:
            return OCRExtractDTO(text_boxes=[], error="Model not loaded")

        try:
            logger.info("EasyOCR 실행 시작")

            # EasyOCR 실행
            result = self.model.readtext(image_data)

            # 결과 파싱
            text_boxes = []
            for detection in result:
                bbox = detection[0]
                text = detection[1]
                confidence = detection[2]

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

            return OCRExtractDTO(
                text_boxes=text_boxes,
            )

        except Exception as e:
            logger.error(f"EasyOCR predict 실행 중 오류: {str(e)}")
            return OCRExtractDTO(text_boxes=[], error=str(e))

    def predict_batch(
        self, image_data_list: List[bytes], confidence_threshold: float
    ) -> List[OCRExtractDTO]:
        if not self.is_loaded or self.model is None:
            return [OCRExtractDTO(text_boxes=[], error="Model not loaded")]

        result = self.model.readtext_batched(image_data_list)
        return result
