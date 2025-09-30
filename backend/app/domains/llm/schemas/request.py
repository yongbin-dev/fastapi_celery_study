# app/domains/llm/schemas/request.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class LLMPredictRequest(BaseModel):
    """LLM 예측 요청 스키마"""

    prompt: str = Field(..., description="입력 프롬프트", min_length=1)
    model: str = Field(default="gpt-3.5-turbo", description="사용할 모델 이름")
    max_tokens: Optional[int] = Field(default=2000, ge=1, le=4000, description="최대 토큰 수")
    temperature: Optional[float] = Field(
        default=0.7, ge=0.0, le=2.0, description="생성 온도"
    )
    options: Optional[Dict[str, Any]] = Field(default=None, description="추가 옵션")


class LLMChatRequest(BaseModel):
    """LLM 채팅 요청 스키마"""

    message: str = Field(..., description="사용자 메시지", min_length=1)
    conversation_id: Optional[str] = Field(default=None, description="대화 ID")
    model: str = Field(default="gpt-3.5-turbo", description="사용할 모델 이름")
    max_length: Optional[int] = Field(default=100, ge=10, le=500, description="최대 응답 길이")