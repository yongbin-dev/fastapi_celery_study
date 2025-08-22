# ai/llm_model.py
from .base_model import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import Dict, Any

class LLMModel(BaseModel):
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        super().__init__()
        self.model_name = model_name
        self.tokenizer = None

    def load_model(self):
        """모델 로드"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            self.is_loaded = True
            print(f"Model {self.model_name} loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.is_loaded = False

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """예측 실행"""
        if not self.is_loaded:
            return {"error": "Model not loaded"}

        message = input_data.get("message", "")
        max_length = input_data.get("max_length", 100)

        try:
            # 토큰화
            inputs = self.tokenizer.encode(message, return_tensors="pt")

            # 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=max_length,
                    temperature=0.7,
                    pad_token_id=self.tokenizer.eos_token_id,
                    do_sample=True
                )

            # 디코딩
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            return {"response.py": response, "status": "success"}

        except Exception as e:
            return {"error": str(e), "status": "failed"}