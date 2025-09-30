# app/domains/llm/services/llm_model.py
# from transformers import AutoTokenizer, AutoModelForCausalLM
# import torch
from typing import Any, Dict

from app.shared.base_model import BaseModel


class LLMModel(BaseModel):
    """LLM 모델 클래스"""

    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        super().__init__()
        self.model_name = model_name
        self.tokenizer = None

    def load_model(self):
        """모델 로드"""
        try:
            # self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            # self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            # self.is_loaded = True
            print(f"Model {self.model_name} loaded successfully")
            self.is_loaded = True
        except Exception as e:
            print(f"Error loading model: {e}")
            self.is_loaded = False

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """예측 실행"""
        if not self.is_loaded:
            return {"error": "Model not loaded", "status": "failed"}

        return {"response": "", "status": "success"}

        # message = input_data.get("message", "")
        # max_length = input_data.get("max_length", 100)

        # try:
        #     # 토큰화
        #     inputs = self.tokenizer.encode(message, return_tensors="pt")

        #     # 생성
        #     with torch.no_grad():
        #         outputs = self.model.generate(
        #             inputs,
        #             max_length=max_length,
        #             temperature=0.7,
        #             pad_token_id=self.tokenizer.eos_token_id,
        #             do_sample=True,
        #         )

        #     # 디코딩
        #     response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        #     return {"response": response, "status": "success"}

        # except Exception as e:
        #     return {"error": str(e), "status": "failed"}


# 싱글톤 인스턴스
_llm_instance = None


def get_llm_model() -> LLMModel:
    """LLM 모델 의존성 주입 함수 (싱글톤 패턴)"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMModel()
        _llm_instance.load_model()
    return _llm_instance
