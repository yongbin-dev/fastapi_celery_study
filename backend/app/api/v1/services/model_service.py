# services/model_service.py
from typing import Dict, Any, Optional, List
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class OllamaModelWrapper:
    """Ollama 모델을 위한 래퍼 클래스"""

    def __init__(self, model_name: str, base_url: Optional[str] = None):
        self.model_name = model_name
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.llm = None

    def load_model(self):
        """모델 로드"""
        try:
            self.llm = OllamaLLM(model=self.model_name, base_url=self.base_url)
            logger.info(f"Ollama 모델 '{self.model_name}' 로드 완료")
            return True
        except Exception as e:
            logger.error(f"Ollama 모델 '{self.model_name}' 로드 실패: {e}")
            return False

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """예측 실행"""
        if not self.llm:
            return {"error": "모델이 로드되지 않았습니다"}

        try:
            # 입력 데이터에서 프롬프트 추출
            prompt_text = input_data.get("prompt", input_data.get("question", ""))
            if not prompt_text:
                return {"error": "프롬프트 또는 질문이 필요합니다"}

            # 템플릿이 있으면 사용, 없으면 직접 실행
            template = input_data.get("template")
            if template:
                prompt = PromptTemplate.from_template(template)
                chain = prompt | self.llm
                result = chain.invoke({"question": prompt_text})
            else:
                result = self.llm.invoke(prompt_text)

            return {"model": self.model_name, "response": result, "status": "success"}
        except Exception as e:
            logger.error(f"예측 실행 중 오류: {e}")
            return {"error": f"예측 실행 실패: {str(e)}"}


class ModelService:
    def __init__(self):
        self.models: Dict[str, OllamaModelWrapper] = {}
        self._initialize_default_models()

    def _initialize_default_models(self):
        """기본 Ollama 모델들 초기화"""
        default_models = ["llama3", "llama2", "phi3", "deepseek-r1"]
        for model_name in default_models:
            self.add_ollama_model(model_name)

    def add_model(self, name: str, model_instance):
        """모델 추가"""
        self.models[name] = model_instance
        success = model_instance.load_model()
        if success:
            logger.info(f"모델 '{name}' 추가 완료")
        else:
            logger.warning(f"모델 '{name}' 추가 실패")

    def add_ollama_model(self, model_name: str, base_url: Optional[str] = None) -> bool:
        """Ollama 모델 추가"""
        model_wrapper = OllamaModelWrapper(model_name, base_url)
        self.models[model_name] = model_wrapper
        return model_wrapper.load_model()

    def get_model(self, name: str) -> Optional[OllamaModelWrapper]:
        """모델 가져오기"""
        return self.models.get(name)

    def predict(self, model_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """예측 실행"""
        model = self.get_model(model_name)
        if not model:
            available_models = list(self.models.keys())
            return {
                "error": f"모델 '{model_name}'을 찾을 수 없습니다",
                "available_models": available_models,
            }

        return model.predict(input_data)

    def list_models(self) -> List[str]:
        """로드된 모델 목록"""
        return list(self.models.keys())

    def remove_model(self, name: str) -> bool:
        """모델 제거"""
        if name in self.models:
            del self.models[name]
            logger.info(f"모델 '{name}' 제거 완료")
            return True
        return False

    def get_model_info(self, name: str) -> Dict[str, Any]:
        """모델 정보 반환"""
        model = self.get_model(name)
        if not model:
            return {"error": f"모델 '{name}'을 찾을 수 없습니다"}

        return {
            "name": model.model_name,
            "base_url": model.base_url,
            "loaded": model.llm is not None,
            "status": "ready" if model.llm else "not_loaded",
        }


# 전역 서비스 인스턴스
model_service = ModelService()


# 의존성 주입 함수
def get_model_service() -> ModelService:
    return model_service
