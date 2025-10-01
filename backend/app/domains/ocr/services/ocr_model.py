# app/domains/ocr/services/ocr_model.py
from typing import Optional

from app.config import settings
from app.core.logging import get_logger
from app.domains.ocr.services.engines.base import BaseOCREngine
from app.shared.base_model import BaseModel

from ..schemas import OCRResultDTO
from .engines import OCREngineFactory

logger = get_logger(__name__)


class OCRModel(BaseModel):
    """OCR 모델 클래스 (Strategy Pattern)"""

    def __init__(self, use_angle_cls: bool = True, lang: str = "korean"):
        super().__init__()
        self.use_angle_cls = use_angle_cls
        self.lang = lang
        self.engine: Optional[BaseOCREngine] = None

    def load_model(self) -> None:
        """모델 로드"""
        # Factory를 통해 적절한 엔진 생성
        self.engine = OCREngineFactory.create_engine(
            engine_type=settings.OCR_ENGINE,
            use_angle_cls=self.use_angle_cls,
            lang=self.lang,
        )

        if self.engine is None:
            logger.error("OCR 엔진 생성 실패")
            self.is_loaded = False
            return

        # 엔진 모델 로드
        self.engine.load_model()
        self.is_loaded = self.engine.is_loaded

        if self.is_loaded:
            logger.info(f"{self.engine.get_engine_name()} 엔진 로드 완료")
        else:
            logger.error(f"{self.engine.get_engine_name()} 엔진 로드 실패")

    def predict(
        self, image_data: bytes, confidence_threshold: float = 0.5
    ) -> OCRResultDTO:
        """OCR 텍스트 추출 실행"""
        if not self.is_loaded or self.engine is None:
            return OCRResultDTO(
                text_boxes=[], full_text="", status="failed", error="Model not loaded"
            )

        # 엔진에 위임
        return self.engine.predict(image_data, confidence_threshold)


# 싱글톤 인스턴스
_ocr_instance: Optional[OCRModel] = None


def get_ocr_model(use_angle_cls: bool = True, lang: str = "korean") -> OCRModel:
    """OCR 모델 의존성 주입 함수 (싱글톤 패턴)"""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = OCRModel(use_angle_cls=use_angle_cls, lang=lang)
        _ocr_instance.load_model()
    return _ocr_instance
