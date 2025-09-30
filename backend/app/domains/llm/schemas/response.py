# app/domains/llm/schemas/response.py
from pydantic import BaseModel, Field
from typing import Optional


class LLMPredictResponse(BaseModel):
    """LLM 예측 응답 스키마"""

    task_id: str = Field(..., description="Celery 태스크 ID")
    status: str = Field(..., description="태스크 상태")
    result: Optional[str] = Field(default=None, description="생성된 텍스트")


class LLMChatResponse(BaseModel):
    """LLM 채팅 응답 스키마"""

    response: str = Field(..., description="LLM 응답 메시지")
    status: str = Field(..., description="처리 상태")
    conversation_id: Optional[str] = Field(default=None, description="대화 ID")