# app/domains/llm/services/llm_service.py
from typing import Any, Dict

from app.shared.base_service import BaseService


class LLMService(BaseService):
    """LLM 비즈니스 로직 서비스"""

    def __init__(self):
        super().__init__()

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """LLM 입력 데이터 검증"""
        if "prompt" not in input_data and "message" not in input_data:
            return False
        return True

    def preprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """전처리: 프롬프트 정제"""
        if "prompt" in input_data:
            input_data["prompt"] = input_data["prompt"].strip()
        if "message" in input_data:
            input_data["message"] = input_data["message"].strip()
        return input_data


llm_service = LLMService()


def get_llm_service():
    return llm_service
