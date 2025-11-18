"""Celery 태스크 상태 조회 스키마

Celery 태스크 실행 상태 조회를 위한 스키마 정의
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from shared.schemas.custom_base_model import CustomBaseModel


class ActiveTaskInfo(CustomBaseModel):
    """현재 실행 중인 태스크 정보

    Attributes:
        task_id: Celery task ID
        task_name: Task 이름
        worker_name: 워커 이름
        time_start: 시작 시간 (timestamp)
        args: Task 인자
        kwargs: Task 키워드 인자
        acknowledged: 워커가 태스크를 확인했는지 여부
    """

    task_id: str = Field(..., description="Celery task ID")
    task_name: str = Field(..., description="Task 이름")
    worker_name: str = Field(..., description="워커 이름")
    time_start: Optional[float] = Field(None, description="시작 시간 (timestamp)")
    args: list[Any] = Field(default_factory=list, description="Task 인자")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Task 키워드 인자")
    acknowledged: bool = Field(default=False, description="워커 확인 여부")


class ActiveTasksResponse(CustomBaseModel):
    """현재 실행 중인 태스크 목록 응답

    Attributes:
        total_active_tasks: 전체 실행 중인 태스크 수
        tasks: 태스크 정보 리스트
        workers: 워커별 태스크 수
    """

    total_active_tasks: int = Field(..., description="전체 실행 중인 태스크 수")
    tasks: list[ActiveTaskInfo] = Field(
        default_factory=list, description="태스크 정보 리스트"
    )
    workers: Dict[str, int] = Field(
        default_factory=dict, description="워커별 태스크 수"
    )


class ScheduledTaskInfo(BaseModel):
    """예약된 태스크 정보

    Attributes:
        task_id: Celery task ID
        task_name: Task 이름
        worker_name: 워커 이름
        eta: 예상 실행 시간 (timestamp)
        args: Task 인자
        kwargs: Task 키워드 인자
        priority: 우선순위
    """

    task_id: str = Field(..., description="Celery task ID")
    task_name: str = Field(..., description="Task 이름")
    worker_name: str = Field(..., description="워커 이름")
    eta: Optional[float] = Field(None, description="예상 실행 시간 (timestamp)")
    args: list[Any] = Field(default_factory=list, description="Task 인자")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Task 키워드 인자")
    priority: Optional[int] = Field(None, description="우선순위")


class ScheduledTasksResponse(BaseModel):
    """예약된 태스크 목록 응답

    Attributes:
        total_scheduled_tasks: 전체 예약된 태스크 수
        tasks: 태스크 정보 리스트
        workers: 워커별 태스크 수
    """

    total_scheduled_tasks: int = Field(..., description="전체 예약된 태스크 수")
    tasks: list[ScheduledTaskInfo] = Field(
        default_factory=list, description="태스크 정보 리스트"
    )
    workers: Dict[str, int] = Field(
        default_factory=dict, description="워커별 태스크 수"
    )


class ReservedTaskInfo(BaseModel):
    """대기 중인 태스크 정보

    Attributes:
        task_id: Celery task ID
        task_name: Task 이름
        worker_name: 워커 이름
        args: Task 인자
        kwargs: Task 키워드 인자
        acknowledged: 워커가 태스크를 확인했는지 여부
    """

    task_id: str = Field(..., description="Celery task ID")
    task_name: str = Field(..., description="Task 이름")
    worker_name: str = Field(..., description="워커 이름")
    args: list[Any] = Field(default_factory=list, description="Task 인자")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Task 키워드 인자")
    acknowledged: bool = Field(default=False, description="워커 확인 여부")


class ReservedTasksResponse(BaseModel):
    """대기 중인 태스크 목록 응답

    Attributes:
        total_reserved_tasks: 전체 대기 중인 태스크 수
        tasks: 태스크 정보 리스트
        workers: 워커별 태스크 수
    """

    total_reserved_tasks: int = Field(..., description="전체 대기 중인 태스크 수")
    tasks: list[ReservedTaskInfo] = Field(
        default_factory=list, description="태스크 정보 리스트"
    )
    workers: Dict[str, int] = Field(
        default_factory=dict, description="워커별 태스크 수"
    )


class AllTasksStatusResponse(BaseModel):
    """전체 태스크 상태 응답

    Attributes:
        active: 실행 중인 태스크 정보
        scheduled: 예약된 태스크 정보
        reserved: 대기 중인 태스크 정보
        total_tasks: 전체 태스크 수
    """

    active: ActiveTasksResponse = Field(..., description="실행 중인 태스크")
    scheduled: ScheduledTasksResponse = Field(..., description="예약된 태스크")
    reserved: ReservedTasksResponse = Field(..., description="대기 중인 태스크")
    total_tasks: int = Field(..., description="전체 태스크 수")
