
from sqlalchemy import Column, String, Integer, DateTime, Text
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
        args: str = None,
        kwargs: str = None,
        result: str = None,
        error_message: str = None,
        traceback: str = None,
        retry_count: int = 0,
        task_time: Optional[datetime] = None,
        completed_time: Optional[datetime] = None,
        **extra_kwargs
    ):
        super().__init__(**extra_kwargs)
        self.task_id = task_id
        self.status = status
        self.task_name = task_name
        self.args = args
        self.kwargs = kwargs
        self.result = result
        self.error_message = error_message
        self.traceback = traceback
        self.retry_count = retry_count
        self.task_time = task_time or datetime.now()
        self.completed_time = completed_time



    def dict(self):
        """모델을 딕셔너리로 변환"""
        return TaskInfoResponse (
            # id = self.id,
            task_id = self.task_id,
            status=self.status ,
            task_name=self.task_name,
            kwargs="",
            args=self.args ,
            result=self.result ,
            error_message="",
            traceback="",
            retry_count=self.retry_count,
            task_time=self.task_time.isoformat(),
            completed_time=self.completed_time.isoformat()
        )
