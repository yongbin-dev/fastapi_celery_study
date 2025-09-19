# models/task_execution_history.py
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class TaskExecutionHistory(Base):
    """
    작업 실행 이력 테이블
    작업의 각 시도(재시도 포함)에 대한 상세 기록
    """

    __tablename__ = "task_execution_history"

    # 기본 필드
    id = Column(Integer, primary_key=True, comment="고유 식별자")
    task_id = Column(
        String(255),
        ForeignKey("task_logs.task_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="작업 ID (외래키)",
    )

    # 시도 정보
    attempt_number = Column(
        Integer, nullable=False, index=True, comment="시도 번호 (1부터 시작)"
    )
    status = Column(String(50), nullable=False, comment="시도 결과 상태")

    # 시간 추적
    started_at = Column(DateTime, comment="시도 시작 시간")
    completed_at = Column(DateTime, comment="시도 완료 시간")

    # 에러 정보
    error_message = Column(Text, comment="에러 메시지")
    traceback = Column(Text, comment="스택 트레이스")

    # 메타데이터
    created_at = Column(DateTime, default=datetime.now, comment="레코드 생성 시간")

    # 관계 설정
    task = relationship("TaskLog", back_populates="execution_history")

    # 인덱스 정의
    __table_args__ = (
        Index("idx_execution_task_attempt", "task_id", "attempt_number"),
        Index("idx_execution_status_created", "status", "created_at"),
    )

    def __repr__(self):
        return f"<TaskExecutionHistory(task_id={self.task_id}, attempt={self.attempt_number}, status={self.status})>"

    @property
    def duration(self):
        """시도 실행 시간 (초)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_successful(self):
        """성공 여부"""
        return self.status == "SUCCESS"

    @property
    def is_failed(self):
        """실패 여부"""
        return self.status in ["FAILURE", "TIMEOUT"]

    @property
    def has_error(self):
        """에러 존재 여부"""
        return bool(self.error_message or self.traceback)

    def get_error_summary(self):
        """에러 요약 반환"""
        if not self.has_error:
            return None

        # 에러 메시지의 첫 줄만 반환
        if self.error_message:
            return self.error_message.split("\n")[0][:200]
        return "Unknown error"

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "attempt_number": self.attempt_number,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration": self.duration,
            "error_message": self.error_message,
            "error_summary": self.get_error_summary(),
            "has_traceback": bool(self.traceback),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def create_attempt(cls, task_id, attempt_number, status="STARTED"):
        """새 시도 생성 헬퍼"""
        return cls(
            task_id=task_id,
            attempt_number=attempt_number,
            status=status,
            started_at=datetime.now(),
        )
