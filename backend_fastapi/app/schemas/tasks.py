# schemas/tasks_router.py

from pydantic import BaseModel
from typing import Optional


class TaskRequest(BaseModel):
    """태스크 요청 모델"""
    message: str
    delay: int = 5


class AITaskRequest(BaseModel):
    """AI 태스크 요청 모델"""
    text: str
    max_length: int = 100


class EmailTaskRequest(BaseModel):
    """이메일 태스크 요청 모델"""
    to_email: str
    subject: str
    body: str


class LongTaskRequest(BaseModel):
    """긴 태스크 요청 모델"""
    total_steps: int = 10


class TaskResponse(BaseModel):
    """태스크 응답 모델"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """태스크 상태 응답 모델"""
    task_id: str
    status: str
    message: str
    current: Optional[int] = None
    total: Optional[int] = None
    result: Optional[dict] = None
    error: Optional[str] = None


class TaskStatistics(BaseModel):
    """태스크 통계 모델"""
    total_found: int
    returned_count: int
    time_range: str
    by_status: dict[str, int]
    by_task_type: dict[str, int]
    current_active: dict[str, int]
    workers: list[str]


class TaskFilters(BaseModel):
    """태스크 필터 정보 모델"""
    hours: int
    status: Optional[str] = None
    task_name: Optional[str] = None
    limit: int


class TaskInfoResponse(BaseModel):
    # id : int

    task_id: str
    status: str
    task_name: str
    args: str
    kwargs: str
    result: str
    error_message: str
    traceback: str
    retry_count: int
    task_time: str
    completed_time: str

    # status : str
    # task_name : str
    # date_done : str
    # result : str
    # traceback : str
    # task_time : str

class TaskHistoryResponse(BaseModel):
    """태스크 히스토리 응답 모델"""
    tasks: list[TaskInfoResponse]


# AI 파이프라인 관련 스키마
from enum import Enum
from datetime import datetime


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


class StageStatus(BaseModel):
    """각 단계별 상태 정보"""
    stage: int
    stage_name: str
    status: str
    progress: int = 0
    message: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[float] = None  # 초 단위
    error: Optional[str] = None


class PipelineProgress(BaseModel):
    """파이프라인 전체 진행 상태"""
    pipeline_id: str
    current_stage: int
    total_stages: int = 4
    overall_progress: int = 0  # 0-100
    stages: list[StageStatus] = []
    start_time: Optional[str] = None
    estimated_completion: Optional[str] = None


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


class PipelineStatusResponse(BaseModel):
    """파이프라인 상태 응답"""
    pipeline_id: str
    status: str
    current_stage: int
    current_stage_name: str
    overall_progress: int
    stages: list[StageStatus]
    result: Optional[dict] = None
    error: Optional[str] = None