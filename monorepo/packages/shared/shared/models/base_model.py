from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseModel(ABC):
    """모든 AI 모델의 베이스 클래스"""

    def __init__(self):
        self.model = None
        self.is_loaded = False

    @abstractmethod
    def load_model(self):
        """모델 로드 (추상 메서드)"""
        pass

    @abstractmethod
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """예측 실행 (추상 메서드)"""
        pass

    def unload_model(self):
        """모델 언로드"""
        if self.model is not None:
            del self.model
            self.model = None
            self.is_loaded = False
