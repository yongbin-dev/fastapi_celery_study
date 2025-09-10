
from typing import Optional

from sqlalchemy import Column, String, Integer, Text, Boolean
from sqlalchemy.orm import relationship

from .base import Base


class PipelineExecution(Base):
    __tablename__ = "pipeline_executions"

    id = Column(Integer, primary_key=True, index=True)
    
    # 파이프라인 실행 기본 정보
    execution_id = Column(String(255), unique=True, index=True, nullable=True, comment="Celery 실행 ID")
    pipeline_id = Column(String(255), index=True, nullable=True, comment="파이프라인 템플릿 ID")
    status = Column(String(255), nullable=True, comment="전체 파이프라인 상태")
    
    # 진행 상황
    current_step = Column(Integer, nullable=True, comment="현재 실행 중인 단계 번호")
    is_ready = Column(Boolean, default=False, comment="파이프라인 준비 완료 상태") 
    overall_progress = Column(Integer, default=0, comment="전체 진행률 (0-100)")
    
    # 에러 정보
    error_traceback = Column(Text, nullable=True, comment="에러 트레이스백")
    
    # 하위 호환성을 위한 deprecated 필드
    stages_json = Column(Text, nullable=True, comment="단계 정보 JSON (deprecated, pipeline_stages 테이블 사용)")
    
    # 관계 설정 (1:N)
    stages = relationship("PipelineStage", back_populates="pipeline_execution", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PipelineExecution(execution_id='{self.execution_id}', status='{self.status}', current_step='{self.current_step}')>"

    def __init__(
        self,
        execution_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
        current_step: Optional[int] = None,
        is_ready: Optional[bool] = False,
        overall_progress: Optional[int] = 0,
        error_traceback: Optional[str] = None,
        stages_json: Optional[str] = None,
        # 하위 호환성 파라미터들
        task_id: Optional[str] = None,  # execution_id로 매핑
        stages: Optional[str] = None,   # stages_json으로 매핑
        traceback: Optional[str] = None, # error_traceback으로 매핑
        step: Optional[int] = None,     # current_step으로 매핑
        ready: Optional[bool] = None,   # is_ready로 매핑
        progress: Optional[int] = None, # overall_progress로 매핑
        **extra_kwargs
    ):
        super().__init__(**extra_kwargs)
        
        # 새로운 필드명 우선 사용, 없으면 하위 호환 필드명 사용
        self.execution_id = execution_id or task_id
        self.pipeline_id = pipeline_id
        self.status = status
        self.current_step = current_step or step
        self.is_ready = is_ready if is_ready is not None else (ready or False)
        self.overall_progress = overall_progress if overall_progress is not None else (progress or 0)
        self.error_traceback = error_traceback or traceback
        self.stages_json = stages_json or stages
    
    # 하위 호환성을 위한 프로퍼티들
    @property
    def task_id(self):
        """하위 호환성: task_id → execution_id"""
        return self.execution_id
    
    @task_id.setter
    def task_id(self, value):
        """하위 호환성: task_id → execution_id"""
        self.execution_id = value
    
    @property
    def step(self):
        """하위 호환성: step → current_step"""
        return self.current_step
    
    @step.setter
    def step(self, value):
        """하위 호환성: step → current_step"""
        self.current_step = value
        
    @property
    def ready(self):
        """하위 호환성: ready → is_ready"""
        return self.is_ready
    
    @ready.setter
    def ready(self, value):
        """하위 호환성: ready → is_ready"""
        self.is_ready = value
        
    @property
    def progress(self):
        """하위 호환성: progress → overall_progress"""
        return self.overall_progress
    
    @progress.setter
    def progress(self, value):
        """하위 호환성: progress → overall_progress"""
        self.overall_progress = value
        
    @property
    def traceback(self):
        """하위 호환성: traceback → error_traceback"""
        return self.error_traceback
    
    @traceback.setter
    def traceback(self, value):
        """하위 호환성: traceback → error_traceback"""
        self.error_traceback = value


# 하위 호환성을 위한 별칭
TaskInfo = PipelineExecution
