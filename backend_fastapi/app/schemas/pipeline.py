# schemas/pipeline.py

from typing import Optional
from pydantic import BaseModel


class AIPipelineRequest(BaseModel):
    """AI 파이프라인 실행 요청"""
    text: str
    options: Optional[dict] = {}
    priority: int = 5  # 1-10, 높을수록 우선순위
    callback_url: Optional[str] = None  # 완료 시 웹훅 URL


class AIPipelineResponse(BaseModel):
    """AI 파이프라인 응답"""
    pipeline_id: str
    status: str
    message: str
    estimated_duration: Optional[int] = None  # 예상 소요 시간 (초)