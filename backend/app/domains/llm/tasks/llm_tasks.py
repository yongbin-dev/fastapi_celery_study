# app/domains/llm/tasks/llm_tasks.py
from typing import Dict, Any
from app.celery_app import celery_app
from app.core.logging import get_logger
from ..services.llm_model import LLMModel

logger = get_logger(__name__)


@celery_app.task(bind=True, name="llm.generate_text")
def generate_text_task(self, prompt: str, model_name: str = "microsoft/DialoGPT-medium") -> Dict[str, Any]:
    """
    LLM 텍스트 생성 태스크

    Args:
        prompt: 입력 프롬프트
        model_name: 사용할 모델 이름

    Returns:
        생성된 텍스트 결과
    """
    logger.info(f"LLM 텍스트 생성 시작 - Task ID: {self.request.id}")

    model = LLMModel(model_name=model_name)
    model.load_model()

    result = model.predict({"message": prompt, "max_length": 100})

    logger.info(f"LLM 텍스트 생성 완료 - Task ID: {self.request.id}")
    return result


@celery_app.task(bind=True, name="llm.chat")
def chat_task(self, message: str, conversation_id: str = "") -> Dict[str, Any]:
    """
    LLM 채팅 태스크

    Args:
        message: 사용자 메시지
        conversation_id: 대화 ID (선택)

    Returns:
        LLM 응답
    """
    logger.info(f"LLM 채팅 시작 - Task ID: {self.request.id}")

    model = LLMModel()
    model.load_model()

    result = model.predict({"message": message, "max_length": 100})
    result["conversation_id"] = conversation_id

    logger.info(f"LLM 채팅 완료 - Task ID: {self.request.id}")
    return result
