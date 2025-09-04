
from sqlalchemy import Column, String, Integer, DateTime, Text , JSON
from datetime import datetime
from typing import Optional

from .base import Base
from ..schemas.tasks import TaskInfoResponse


class TaskInfo(Base) :
    __tablename__ = "task_info"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, index=True, nullable=False, comment="Celery 태스크 ID")
    status = Column(String(255), nullable=False, comment="태스크 상태")
    task_name = Column(String(255), nullable=False, comment="태스크 이름")
    args = Column(Text, nullable=True, comment="태스크 인자")
    kwargs = Column(Text, nullable=True, comment="태스크 키워드 인자")
    result = Column(Text, nullable=True, comment="태스크 결과")
    error_message = Column(Text, nullable=True, comment="에러 메시지")
    traceback = Column(Text, nullable=True, comment="트레이스백")
    retry_count = Column(Integer, default=0, comment="재시도 횟수")

    # Chain 관련 필드들
    root_task_id = Column(String, index=True, nullable=True)  # 체인의 루트 태스크
    parent_task_id = Column(String, index=True, nullable=True)  # 직접적인 부모 태스크
    chain_total = Column(Integer, nullable=True)  # 체인의 전체 태스크 수

    def __repr__(self):
        return f"<TaskInfo(task_id='{self.task_id}', status='{self.status}', root_task_id='{self.root_task_id}')>"

    task_time = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        comment="태스크 시작 시간"
    )
    completed_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="태스크 완료 시간"
    )

    def __init__(
        self,
        task_id: str,
        status: str,
        task_name: str,
        **extra_kwargs
    ):
        super().__init__(**extra_kwargs)
        self.task_id = task_id
        self.status = status
        self.task_name = task_name
        self.retry_count = 0
        self.task_time = datetime.now()

    def dict(self):
        """모델을 딕셔너리로 변환"""
        return TaskInfoResponse(
            task_id=self.task_id,
            status=self.status,
            task_name=self.task_name,
            args=self.args or "",
            kwargs=self.kwargs or "",
            result=self.result or "",
            error_message=self.error_message or "",
            traceback=self.traceback or "",
            retry_count=self.retry_count,
            task_time=self.task_time.isoformat() if self.task_time else None,
            completed_time=self.completed_time.isoformat() if self.completed_time else None,
            root_task_id=self.root_task_id or "",
            parent_task_id=self.parent_task_id or "",
            chain_total=self.chain_total or 0,
        )
