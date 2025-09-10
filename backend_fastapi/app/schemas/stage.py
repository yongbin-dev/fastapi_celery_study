# schemas/stage.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from .enums import StageStatus


class StageInfo(BaseModel):
    """Stage 정보 모델"""
    stage: int
    stage_name: str
    status: StageStatus = StageStatus.PENDING
    progress: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = None

    class Config:
        use_enum_values = True  # Enum 값을 문자열로 직렬화
        
    @classmethod
    def create_pending_stage(cls, stage: int, stage_name: str) -> "StageInfo":
        """대기 중인 stage 생성"""
        return cls(
            stage=stage,
            stage_name=stage_name,
            status=StageStatus.PENDING,
            progress=0
        )
    
    @classmethod
    def create_completed_stage(cls, stage: int, stage_name: str, metadata: Optional[dict] = None) -> "StageInfo":
        """완료된 stage 생성"""
        return cls(
            stage=stage,
            stage_name=stage_name,
            status=StageStatus.COMPLETED,
            progress=100,
            completed_at=datetime.now(),
            metadata=metadata or {}
        )
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환 (Redis 저장용)"""
        return {
            "stage": self.stage,
            "stage_name": self.stage_name,
            "status": self.status.value if isinstance(self.status, StageStatus) else self.status,
            "progress": self.progress
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "StageInfo":
        """딕셔너리에서 생성 (Redis 로드용)"""
        return cls(
            stage=data.get("stage", 0),
            stage_name=data.get("stage_name", ""),
            status=StageStatus(data.get("status", "pending")),
            progress=data.get("progress", 0)
        )