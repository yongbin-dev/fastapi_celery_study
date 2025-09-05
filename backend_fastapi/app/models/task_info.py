
from typing import Optional

from sqlalchemy import Column, String, Integer, Text, Boolean

from .base import Base


class TaskInfo(Base) :
    __tablename__ = "task_info"

    id = Column(Integer, primary_key=True, index=True)
    
    # TaskStatusResponse 기반 필드들
    task_id = Column(String(255), unique=True, index=True, nullable=True, comment="Celery 태스크 ID")
    status = Column(String(255), nullable=True, comment="태스크 상태")
    stages = Column(Text, nullable=True, comment="태스크 단계 정보")
    traceback = Column(Text, nullable=True, comment="트레이스백")
    step = Column(Integer, nullable=True, comment="현재 태스크의 단계 번호")
    ready = Column(Boolean, default=False, comment="태스크 준비 상태") 
    progress = Column(Integer, default=0, comment="진행률 (0-100)")
    
    # Pipeline 관련 필드
    pipeline_id = Column(String(255), index=True, nullable=True, comment="파이프라인 ID")

    def __repr__(self):
        return f"<TaskInfo(task_id='{self.task_id}', status='{self.status}', step='{self.step}')>"

    def __init__(
        self,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        stages: Optional[str] = None,
        traceback: Optional[str] = None,
        step: Optional[int] = None,
        ready: Optional[bool] = False,
        progress: Optional[int] = 0,
        pipeline_id: Optional[str] = None,
        **extra_kwargs
    ):
        super().__init__(**extra_kwargs)
        self.task_id = task_id
        self.status = status
        self.stages = stages
        self.traceback = traceback
        self.step = step
        self.ready = ready or False
        self.progress = progress or 0
        self.pipeline_id = pipeline_id
