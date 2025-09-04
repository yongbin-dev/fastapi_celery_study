# schemas/tasks_router.py

from typing import Optional

from pydantic import BaseModel


class TaskRequest(BaseModel):
    """태스크 요청 모델"""
    message: str
    delay: int = 5


class AITaskRequest(BaseModel):
    """AI 태스크 요청 모델"""
    text: str
    max_length: int = 100

class TaskFilters(BaseModel):
    """태스크 필터 정보 모델"""
    hours: int
    status: Optional[str] = None
    task_name: Optional[str] = None
    limit: int

class TaskStatusResponse(BaseModel):
    """태스크 상태 응답 모델"""
    task_id: Optional[str] = None
    status: Optional[str] = None
    task_name: Optional[str] = None
    result: Optional[str] = None
    traceback: Optional[str] = None
    step: Optional[int] = None
    ready: Optional[bool] = False
    progress: Optional[int] = 0

class TaskInfoResponse(BaseModel):
    task_id: str
    status: str
    task_name: str
    args: str
    kwargs: str
    result: str
    error_message: str
    traceback: str
    retry_count: int
    task_time: Optional[str] = None
    completed_time: Optional[str] = None

    # Chain 관련
    root_task_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    chain_total: Optional[int] = None

# AI 파이프라인 관련 스키마
from datetime import datetime


class AIPipelineRequest(BaseModel):
    """AI 파이프라인 실행 요청"""
    text: str
    options: Optional[dict] = {}
    priority: int = 5  # 1-10, 높을수록 우선순위
    callback_url: Optional[str] = None  # 완료 시 웹훅 URL

class PipelineStatusResponse(BaseModel):
    """파이프라인 상태 응답"""
    pipeline_id: str
    overall_state: str
    total_steps: int
    current_stage: Optional[int] = 0
    start_time: Optional[str] = None
    tasks: list[TaskStatusResponse] = []

class AIPipelineResponse(BaseModel):
    """AI 파이프라인 응답"""
    pipeline_id: str
    status: str
    message: str
    estimated_duration: Optional[int] = None  # 예상 소요 시간 (초)

class ChainSummary(BaseModel):
    chain_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    running_tasks: int
    status: str  # RUNNING, COMPLETED, FAILED, PENDING
    started_at: datetime
    completed_at: Optional[datetime] = None
    tasks: list[TaskInfoResponse]


from enum import Enum

class PipelineStage(str, Enum):
    PREPROCESSING = "preprocessing"
    FEATURE_EXTRACTION = "feature_extraction"
    MODEL_INFERENCE = "model_inference"
    POST_PROCESSING = "post_processing"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    PROGRESS = "PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"




