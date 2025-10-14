# app/schemas/task_log.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskLogBase(BaseModel):
    """TaskLog 기본 스키마"""

    id: int
    task_id: str
    task_name: str = Field(..., description="작업 함수명")
    status: str = Field(default="PENDING", description="작업 상태")
    chain_execution_id: Optional[int] = Field(None, description="소속된 체인 실행 ID")


class TaskLogCreate(TaskLogBase):
    """TaskLog 생성용 스키마"""

    task_id: str = Field(..., description="Celery 작업 ID (UUID)")


class TaskLogUpdate(BaseModel):
    """TaskLog 업데이트용 스키마"""

    task_name: Optional[str] = Field(None, description="작업 함수명")
    status: Optional[str] = Field(None, description="작업 상태")
    error: Optional[str] = Field(None, description="에러 메시지")
    started_at: Optional[datetime] = Field(None, description="작업 시작 시간")
    finished_at: Optional[datetime] = Field(None, description="작업 완료 시간")
    retries: Optional[int] = Field(None, description="재시도 횟수")
    chain_execution_id: Optional[int] = Field(None, description="소속된 체인 실행 ID")


class TaskLogResponse(TaskLogBase):
    """TaskLog 응답용 스키마"""

    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
