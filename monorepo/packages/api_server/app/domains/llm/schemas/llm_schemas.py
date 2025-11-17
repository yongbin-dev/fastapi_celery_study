"""LLM 관련 Pydantic 스키마"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """채팅 메시지 스키마"""

    role: str = Field(
        ...,
        description="메시지 역할 (system, user, assistant 등)",
        examples=["user", "assistant", "system"],
    )
    content: str = Field(..., description="메시지 내용", min_length=1)

    model_config = {
        "json_schema_extra": {"example": {"role": "user", "content": "안녕하세요"}}
    }


class ChatCompletionRequest(BaseModel):
    """채팅 완성 요청 스키마"""

    messages: List[ChatMessage] = Field(
        ..., description="대화 메시지 리스트", min_length=1
    )
    model: Optional[str] = Field(
        None,
        description="사용할 LLM 모델 ID (지정하지 않으면 기본 모델 사용)",
        examples=["Qwen/Qwen3-0.6B", "gpt-4"],
    )
    temperature: float = Field(
        0.7,
        description="샘플링 온도 (0.0 ~ 2.0, 높을수록 창의적)",
        ge=0.0,
        le=2.0,
    )
    max_tokens: Optional[int] = Field(
        None, description="최대 생성 토큰 수", gt=0, examples=[512, 1024, 2048]
    )
    stream: bool = Field(False, description="스트리밍 응답 여부")

    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [{"role": "user", "content": "안녕하세요"}],
                "model": "Qwen/Qwen3-0.6B",
                "temperature": 0.7,
                "max_tokens": 512,
                "stream": False,
            }
        }
    }
