# app/domains/ocr/services/similarity/base.py
from abc import ABC, abstractmethod
from typing import Dict


class BaseSimilarity(ABC):
    """유사도 측정 추상 클래스"""

    @abstractmethod
    def calculate(self, text1: str, text2: str) -> float:
        """
        두 텍스트 간의 유사도를 계산합니다.

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            0.0 ~ 1.0 사이의 유사도 점수
        """
        pass

    @abstractmethod
    def get_metrics(self, text1: str, text2: str) -> Dict[str, float]:
        """
        상세한 유사도 메트릭을 반환합니다.

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            메트릭 이름과 값의 딕셔너리
        """
        pass

    @abstractmethod
    def get_method_name(self) -> str:
        """
        유사도 측정 방법의 이름을 반환합니다.

        Returns:
            방법 이름 (예: "string", "token")
        """
        pass
