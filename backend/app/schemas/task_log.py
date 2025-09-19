# app/schemas/task_log.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class TaskLogBase(BaseModel):
    """TaskLog 기본 스키마"""

    task_name: str = Field(..., description="작업 함수명")
    status: str = Field(default="PENDING", description="작업 상태")
    args: Optional[str] = Field(None, description="작업 위치 인자 (JSON 형식)")
    kwargs: Optional[str] = Field(None, description="작업 키워드 인자 (JSON 형식)")
    result: Optional[str] = Field(None, description="작업 실행 결과 (JSON 형식)")
    error: Optional[str] = Field(None, description="에러 메시지")
    retries: Optional[int] = Field(default=0, description="재시도 횟수")
    chain_execution_id: Optional[int] = Field(None, description="소속된 체인 실행 ID")


class TaskLogCreate(TaskLogBase):
    """TaskLog 생성용 스키마"""

    task_id: str = Field(..., description="Celery 작업 ID (UUID)")


class TaskLogUpdate(BaseModel):
    """TaskLog 업데이트용 스키마"""

    task_name: Optional[str] = Field(None, description="작업 함수명")
    status: Optional[str] = Field(None, description="작업 상태")
    args: Optional[str] = Field(None, description="작업 위치 인자 (JSON 형식)")
    kwargs: Optional[str] = Field(None, description="작업 키워드 인자 (JSON 형식)")
    result: Optional[str] = Field(None, description="작업 실행 결과 (JSON 형식)")
    error: Optional[str] = Field(None, description="에러 메시지")
    started_at: Optional[datetime] = Field(None, description="작업 시작 시간")
    completed_at: Optional[datetime] = Field(None, description="작업 완료 시간")
    retries: Optional[int] = Field(None, description="재시도 횟수")
    chain_execution_id: Optional[int] = Field(None, description="소속된 체인 실행 ID")


class TaskLogResponse(TaskLogBase):
    """TaskLog 응답용 스키마"""

    id: int
    task_id: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class TaskLogStats(BaseModel):
    """작업 로그 통계 스키마"""

    total_count: int = Field(..., description="총 작업 수")
    avg_duration: float = Field(..., description="평균 실행 시간 (초)")
    min_duration: float = Field(..., description="최소 실행 시간 (초)")
    max_duration: float = Field(..., description="최대 실행 시간 (초)")


class TaskLogStatusStats(BaseModel):
    """상태별 통계 스키마"""

    PENDING: int = Field(default=0, description="대기 중인 작업 수")
    STARTED: int = Field(default=0, description="시작된 작업 수")
    SUCCESS: int = Field(default=0, description="성공한 작업 수")
    FAILURE: int = Field(default=0, description="실패한 작업 수")
    RETRY: int = Field(default=0, description="재시도 중인 작업 수")
    REVOKED: int = Field(default=0, description="취소된 작업 수")
