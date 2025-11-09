# app/domains/ocr/services/engines/base.py
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from shared.schemas import OCRExtractDTO


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
    def predict(self, image_data: bytes, confidence_threshold: float) -> OCRExtractDTO:
        """
        OCR 예측 수행

        Args:
            image_data: 이미지 데이터 (bytes)
            confidence_threshold: 신뢰도 임계값

        Returns:
            OCRExtractDTO 객체
        """
        pass

    @abstractmethod
    def predict_batch(
        self, image_data_list: List[bytes], confidence_threshold: float
    ) -> List[OCRExtractDTO]:
        """
        여러 이미지에 대한 배치 OCR 예측 수행

        기본 구현은 각 이미지에 대해 순차적으로 predict를 호출합니다.
        각 엔진에서 최적화된 배치 처리를 위해 이 메서드를 오버라이드할 수 있습니다.

        Args:
            image_data_list: 이미지 데이터 리스트 (List[bytes])
            confidence_threshold: 신뢰도 임계값

        Returns:
            OCRExtractDTO 객체 리스트
        """
        pass

    @abstractmethod
    def get_engine_name(self) -> str:
        """엔진 이름 반환"""
        pass
