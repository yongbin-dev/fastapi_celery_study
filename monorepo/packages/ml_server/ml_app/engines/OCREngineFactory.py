from typing import Optional  # noqa: N999

from shared.core.logging import get_logger

from .base import BaseOCREngine
from .easyocr_engine import EasyOCREngine
from .mock_engine import MockOCREngine
from .paddleocr_engine import PaddleOCREngine

logger = get_logger(__name__)


class OCREngineFactory:
    """OCR 엔진 팩토리"""

    _engines = {
        "easyocr": EasyOCREngine,
        "paddleocr": PaddleOCREngine,
        "mock": MockOCREngine,
    }

    @classmethod
    def create_engine(
        cls, engine_type: str, use_angle_cls: bool = True, lang: str = "korean"
    ) -> Optional[BaseOCREngine]:
        """
        OCR 엔진 생성

        Args:
            engine_type: 엔진 타입 ("easyocr", "paddleocr", "mock")
            use_angle_cls: 각도 분류 사용 여부
            lang: 언어

        Returns:
            BaseOCREngine 인스턴스 또는 None

        Note:
            - easyocr: EasyOCR 엔진 (다국어 지원)
            - paddleocr: PaddleOCR 엔진 (중국어 특화)
            - mock: 테스트용 Mock 엔진 (가짜 결과 반환)
        """
        engine_type = engine_type.lower()

        if engine_type not in cls._engines:
            logger.error(f"지원하지 않는 OCR 엔진: {engine_type}")
            logger.info(f"사용 가능한 엔진: {list(cls._engines.keys())}")
            return None

        engine_class = cls._engines[engine_type]
        engine = engine_class(use_angle_cls=use_angle_cls, lang=lang)

        logger.info(f"OCR 엔진 생성: {engine.get_engine_name()}")

        return engine

    @classmethod
    def register_engine(cls, name: str, engine_class: type) -> None:
        """
        새로운 엔진 등록 (확장성)

        Args:
            name: 엔진 이름
            engine_class: 엔진 클래스
        """
        cls._engines[name.lower()] = engine_class
        logger.info(f"새로운 OCR 엔진 등록: {name}")

    @classmethod
    def get_available_engines(cls) -> list:
        """사용 가능한 엔진 목록 반환"""
        return list(cls._engines.keys())
