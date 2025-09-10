# app/models/stage.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base


class PipelineStage(Base):
    """파이프라인 단계 정보 모델 (PipelineExecution과 1:N 관계)"""
    
    __tablename__ = "pipeline_stages"
    __table_args__ = (
        {"comment": "파이프라인 단계별 진행 상황"}
    )
    
    # Primary Key
    id = Column(Integer, primary_key=True, comment="Stage ID")
    
    # Foreign Key
    pipeline_execution_id = Column(
        Integer, 
        ForeignKey("pipeline_executions.id", ondelete="CASCADE"),
        nullable=False,
        comment="PipelineExecution ID (외래키)"
    )
    
    # Stage 정보
    stage_number = Column(Integer, nullable=False, comment="Stage 순서 (1, 2, 3, 4)")
    stage_name = Column(String(100), nullable=False, comment="Stage 이름")
    status = Column(
        String(20), 
        nullable=False, 
        default="pending",
        comment="Stage 상태 (pending, running, completed, failed)"
    )
    progress = Column(Integer, nullable=False, default=0, comment="진행률 (0-100)")
    
    # 시간 정보
    started_at = Column(DateTime(timezone=True), nullable=True, comment="Stage 시작 시간")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="Stage 완료 시간")
    
    # 에러 정보
    error_message = Column(Text, nullable=True, comment="에러 메시지")
    
    # 메타데이터 (JSON) - metadata는 SQLAlchemy 예약어이므로 stage_metadata로 변경
    stage_metadata = Column(JSON, nullable=True, comment="Stage 관련 메타데이터")
    
    # 관계 설정
    pipeline_execution = relationship("PipelineExecution", back_populates="stages")
    
    def __repr__(self):
        return f"<PipelineStage(id={self.id}, stage_number={self.stage_number}, stage_name='{self.stage_name}', status='{self.status}')>"
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환 (Redis 호환)"""
        return {
            "stage": self.stage_number,
            "stage_name": self.stage_name,
            "status": self.status,
            "progress": self.progress
        }
    
    @classmethod
    def from_stage_info(cls, stage_info, pipeline_execution_id: int) -> "PipelineStage":
        """StageInfo 스키마에서 PipelineStage 모델 생성"""
        from ..schemas import StageInfo
        
        if isinstance(stage_info, StageInfo):
            return cls(
                pipeline_execution_id=pipeline_execution_id,
                stage_number=stage_info.stage,
                stage_name=stage_info.stage_name,
                status=stage_info.status.value if hasattr(stage_info.status, 'value') else stage_info.status,
                progress=stage_info.progress,
                started_at=stage_info.started_at,
                completed_at=stage_info.completed_at,
                error_message=stage_info.error_message,
                stage_metadata=stage_info.metadata
            )
        return cls(
            pipeline_execution_id=pipeline_execution_id,
            stage_number=stage_info.get("stage", 0),
            stage_name=stage_info.get("stage_name", ""),
            status=stage_info.get("status", "pending"),
            progress=stage_info.get("progress", 0)
        )



# 하위 호환성을 위한 별칭
Stage = PipelineStage