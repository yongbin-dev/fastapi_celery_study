# models/task_log.py
from sqlalchemy import Column, String, Integer, Text, DateTime, Index
from sqlalchemy.orm import relationship
from .base import Base


class TaskLog(Base):
    """
    작업 로그 메인 테이블
    Celery 작업의 전체 생명주기를 추적
    """

    __tablename__ = "task_logs"

    # 기본 필드
    id = Column(Integer, primary_key=True, comment="고유 식별자")
    task_id = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Celery 작업 ID (UUID)",
    )
    task_name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="작업 함수명 (예: app.tasks.send_email)",
    )
    status = Column(
        String(50),
        nullable=False,
        index=True,
        comment="작업 상태 (PENDING/STARTED/SUCCESS/FAILURE/RETRY/REVOKED)",
    )

    # 작업 파라미터
    args = Column(Text, comment="작업 위치 인자 (JSON 형식)")
    kwargs = Column(Text, comment="작업 키워드 인자 (JSON 형식)")

    # 결과 및 에러
    result = Column(Text, comment="작업 실행 결과 (JSON 형식)")
    error = Column(Text, comment="에러 메시지")

    # 시간 추적
    started_at = Column(DateTime, index=True, comment="작업 시작 시간")
    completed_at = Column(DateTime, comment="작업 완료 시간")

    # 재시도 정보
    retries = Column(Integer, default=0, comment="재시도 횟수")

    # 관계 설정
    task_metadata = relationship(
        "TaskMetadata",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",  # 자동으로 조인하여 로드
    )
    execution_history = relationship(
        "TaskExecutionHistory",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskExecutionHistory.attempt_number",
    )
    task_result = relationship(
        "TaskResult", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    dependents = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_task_id",
        back_populates="depends_on",
    )

    # 인덱스 정의
    __table_args__ = (
        Index("idx_task_logs_status_created", "status", "created_at"),
        Index("idx_task_logs_name_status", "task_name", "status"),
        Index("idx_task_logs_started_at_desc", started_at.desc()),
    )

    def __repr__(self):
        return f"<TaskLog(task_id={self.task_id}, name={self.task_name}, status={self.status})>"

    @property
    def duration(self):
        """작업 실행 시간 (초)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_completed(self):
        """작업 완료 여부"""
        return self.status in ["SUCCESS", "FAILURE", "REVOKED"]

    @property
    def is_running(self):
        """작업 실행 중 여부"""
        return self.status == "STARTED"

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status,
            "args": self.args,
            "kwargs": self.kwargs,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration": self.duration,
            "retries": self.retries,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
