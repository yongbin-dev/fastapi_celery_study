# schemas/responses.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from .stage import StageInfo
from .enums import ProcessStatus


class TaskStatusResponse(BaseModel):
    """태스크 상태 응답 모델 (레거시 호환용)"""
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


class PipelineStagesResponse(BaseModel):
    """파이프라인 스테이지 응답 (새로운 구조화된 형태)"""
    chain_id: str
    total_stages: int
    current_stage: Optional[int] = None
    overall_progress: Optional[int] = 0
    stages: List[StageInfo] = []
    
    @property
    def completed_stages(self) -> int:
        """완료된 스테이지 수"""
        return len([
            stage for stage in self.stages 
            if (stage.status.value if hasattr(stage.status, 'value') else stage.status) == ProcessStatus.SUCCESS.value
        ])
    
    @property
    def failed_stages(self) -> int:
        """실패한 스테이지 수"""
        return len([
            stage for stage in self.stages 
            if (stage.status.value if hasattr(stage.status, 'value') else stage.status) == ProcessStatus.FAILURE.value
        ])
    
    @property
    def pending_stages(self) -> int:
        """대기 중인 스테이지 수"""
        return len([
            stage for stage in self.stages 
            if (stage.status.value if hasattr(stage.status, 'value') else stage.status) == ProcessStatus.PENDING.value
        ])


class StageDetailResponse(BaseModel):
    """개별 스테이지 상세 응답"""
    stage_info: StageInfo
    is_current: bool = False
    is_completed: bool = False
    is_failed: bool = False