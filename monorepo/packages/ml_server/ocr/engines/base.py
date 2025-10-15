# app/domains/ocr/services/engines/base.py
from abc import ABC, abstractmethod
from typing import Any, Optional

from shared.schemas import OCRResultDTO


class BaseOCREngine(ABC):
    """OCR 엔진 추상 클래스"""

    def __init__(self, use_angle_cls: bool = True, lang: str = "korean"):
        self.use_angle_cls = use_angle_cls
        self.lang = lang
        self.model: Optional[Any] = None
        self.is_loaded = False

    @abstractmethod
    def load_model(self) -> None:
        """모델 로드"""
        pass

    @abstractmethod
    def predict(self, image_data: bytes, confidence_threshold: float) -> OCRResultDTO:
        """
        OCR 예측 수행

        Args:
            image_data: 이미지 데이터 (bytes)
            confidence_threshold: 신뢰도 임계값

        Returns:
            OCRResultDTO 객체
        """
        pass

    @abstractmethod
    def get_engine_name(self) -> str:
        """엔진 이름 반환"""
        pass
