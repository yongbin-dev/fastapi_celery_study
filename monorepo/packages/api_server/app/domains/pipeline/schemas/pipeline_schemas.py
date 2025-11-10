"""파이프라인 API 스키마

Request/Response 스키마 정의
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TaskInfo(BaseModel):
    """Task 정보

    Attributes:
        task_id: Celery task ID
        task_name: Task 이름
        status: Task 상태
        retries: 재시도 횟수
        error: 에러 메시지
        started_at: 시작 시간
        finished_at: 완료 시간
    """

    task_id: str = Field(..., description="Celery task ID")
    task_name: str = Field(..., description="Task 이름")
    status: str = Field(..., description="Task 상태")
    retries: int = Field(default=0, description="재시도 횟수")
    error: Optional[str] = Field(None, description="에러 메시지")
    started_at: Optional[datetime] = Field(None, description="시작 시간")
    finished_at: Optional[datetime] = Field(None, description="완료 시간")


class PipelineStatusResponse(BaseModel):
    """파이프라인 상태 응답

    Attributes:
        context_id: 파이프라인 컨텍스트 ID
        status: 현재 상태
        current_stage: 현재 실행 중인 스테이지
        error: 에러 메시지 (있는 경우)
        progress: 진행률 (0.0-1.0)
        result: 최종 결과 (완료 시)
        created_at: 생성 시간
        updated_at: 마지막 업데이트 시간
        total_tasks: 총 작업 수
        completed_tasks: 완료된 작업 수
        failed_tasks: 실패한 작업 수
        tasks: Task 상세 정보 리스트
    """

    context_id: str = Field(..., description="파이프라인 컨텍스트 ID")
    status: str = Field(..., description="현재 상태")
    current_stage: Optional[str] = Field(None, description="현재 실행 중인 스테이지")
    error: Optional[str] = Field(None, description="에러 메시지")
    progress: float = Field(..., ge=0.0, le=1.0, description="진행률")
    result: Optional[Dict[str, Any]] = Field(None, description="최종 결과")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="마지막 업데이트 시간")
    total_tasks: int = Field(..., description="총 작업 수")
    completed_tasks: int = Field(..., description="완료된 작업 수")
    failed_tasks: int = Field(..., description="실패한 작업 수")
    tasks: list[TaskInfo] = Field(default_factory=list, description="Task 상세 정보")


class PipelineHistoryResponse(BaseModel):
    """파이프라인 실행 이력 응답

    Attributes:
        chain_id: Chain ID
        chain_name: Chain 이름
        status: 상태
        completed_tasks: 완료된 작업 수
        total_tasks: 총 작업 수
        started_at: 시작 시간
        finished_at: 완료 시간
    """

    chain_id: str = Field(..., description="Chain ID")
    chain_name: str = Field(..., description="Chain 이름")
    status: str = Field(..., description="상태")
    completed_tasks: int = Field(..., description="완료된 작업 수")
    total_tasks: int = Field(..., description="총 작업 수")
    started_at: Optional[datetime] = Field(None, description="시작 시간")
    finished_at: Optional[datetime] = Field(None, description="완료 시간")
