# schemas/responses.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TaskStatusResponse(BaseModel):
    """태스크 상태 응답 모델"""
    task_id: Optional[str] = None
    status: Optional[str] = None
    task_name: Optional[str] = None
    stages: Optional[str] = None
    traceback: Optional[str] = None
    step: Optional[int] = None
    ready: Optional[bool] = False
    progress: Optional[int] = 0


class PipelineStatusResponse(BaseModel):
    """파이프라인 상태 응답"""
    pipeline_id: str
    overall_state: str
    total_steps: int
    current_stage: Optional[int] = 0
    start_time: Optional[datetime] = None
    tasks: list[TaskStatusResponse] = []