# services/model_service.py
from typing import Dict, Any


class ModelService:
    def __init__(self):
        self.models = {}

    def add_model(self, name: str, model_instance):
        """모델 추가"""
        self.models[name] = model_instance
        model_instance.load_model()

    def get_model(self, name: str):
        """모델 가져오기"""
        return self.models.get(name)

    def predict(self, model_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """예측 실행"""
        model = self.get_model(model_name)
        if not model:
            return {"error": f"Model {model_name} not found"}

        return model.predict(input_data)

    def list_models(self) -> list:
        """로드된 모델 목록"""
        return list(self.models.keys())


# 전역 서비스 인스턴스
model_service = ModelService()