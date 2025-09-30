# app/domains/llm/schemas/__init__.py
"""
LLM 도메인 Pydantic 스키마
"""

from .request import LLMChatRequest, LLMPredictRequest
from .response import LLMChatResponse, LLMPredictResponse

__all__ = [
    "LLMPredictRequest",
    "LLMChatRequest",
    "LLMPredictResponse",
    "LLMChatResponse",
]
