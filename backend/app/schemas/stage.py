# schemas/stage.py

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ValidationError
import time

from .enums import ProcessStatus


class StageInfo(BaseModel):
    """Stage 정보 모델"""

    chain_id: str
    stage: int
    stage_name: str
    task_id: Optional[str] = None  # Celery Task ID
    status: ProcessStatus = ProcessStatus.PENDING
    progress: int = 0
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    updated_at: float = Field(default_factory=time.time)
    error_message: Optional[str] = None
    description: Optional[str] = None
    expected_duration: Optional[str] = None

    model_config = {"use_enum_values": True}  # Enum 값을 문자열로 직렬화

    @classmethod
    def create_pending_stage(
        cls,
        chain_id: str,
        stage: int,
        stage_name: str,
        description: str = "",
        expected_duration: str = "",
    ) -> "StageInfo":
        """대기 중인 stage 생성"""
        return cls(
            chain_id=chain_id,
            stage=stage,
            stage_name=stage_name,
            status=ProcessStatus.PENDING,
            progress=0,
            description=description if description else None,
            expected_duration=expected_duration if expected_duration else None,
        )

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (Redis 저장용)"""
        data = {
            "chain_id": self.chain_id,
            "stage": self.stage,
            "stage_name": self.stage_name,
            "task_id": self.task_id,
            "status": (
                self.status.value
                if isinstance(self.status, ProcessStatus)
                else self.status
            ),
            "progress": self.progress,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
        }

        if self.description is not None:
            data["description"] = self.description

        if self.expected_duration is not None:
            data["expected_duration"] = self.expected_duration

        if self.error_message is not None:
            data["error_message"] = self.error_message

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "StageInfo":
        """딕셔너리에서 생성 (Redis 로드용)"""
        return cls(
            chain_id=data.get("chain_id", ""),
            stage=data.get("stage", 0),
            stage_name=data.get("stage_name", ""),
            task_id=data.get("task_id"),
            status=ProcessStatus(data.get("status", "pending")),
            progress=data.get("progress", 0),
            created_at=data.get("created_at", time.time()),
            started_at=data.get("started_at"),
            updated_at=data.get("updated_at", time.time()),
            error_message=data.get("error_message"),
            description=data.get("description"),
            expected_duration=data.get("expected_duration"),
        )
