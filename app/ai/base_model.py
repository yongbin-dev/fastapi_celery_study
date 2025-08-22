# ai/base_model.py
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseModel(ABC):
    def __init__(self):
        self.model = None
        self.is_loaded = False

    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    def predict(self, input_data: Any) -> Dict[str, Any]:
        pass

    def is_model_loaded(self) -> bool:
        return self.is_loaded