from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from ..schemas.enums import ProcessStatus
from .base import Base


class ChainExecution(Base):
    """
    체인 실행 테이블
    Celery 체인(workflow) 실행 상태 및 결과를 추적
    """

    __tablename__ = "chain_executions"

    # 기본 필드
    id = Column(Integer, primary_key=True, comment="고유 식별자")
    chain_id: Column[str] = Column(
        String(255), nullable=True, index=True, comment="체인 고유 ID"
    )
    chain_name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="체인 이름 (예: user_signup_workflow)",
    )

    # 상태 관리
    status = Column(
        String(20),
        default=ProcessStatus.PENDING,
        nullable=False,
        index=True,
        comment="체인 실행 상태",
    )

    # 작업 통계
    total_tasks = Column(
        Integer, default=0, nullable=False, comment="체인 내 총 작업 수"
    )
    completed_tasks = Column(
        Integer, default=0, nullable=False, comment="완료된 작업 수"
    )
    failed_tasks = Column(Integer, default=0, nullable=False, comment="실패한 작업 수")

    # 타임스탬프
    started_at = Column(DateTime, nullable=True, comment="시작 시간")
    finished_at = Column(DateTime, nullable=True, comment="완료 시간")

    # 메타 정보
    initiated_by = Column(String(100), nullable=True, comment="시작한 사용자/시스템")
    input_data = Column(JSON, nullable=True, comment="입력 데이터 (JSON)")
    final_result = Column(JSON, nullable=True, comment="최종 결과 (JSON)")
    error_message = Column(Text, nullable=True, comment="오류 메시지")

    # 관계 정의
    task_logs = relationship(
        "TaskLog",
        back_populates="chain_execution",
        foreign_keys="TaskLog.chain_execution_id",
        cascade="all, delete-orphan",
        order_by="TaskLog.started_at",
    )

    # 인덱스 정의
    __table_args__ = (
        Index("idx_chain_status_started", "status", "started_at"),
        Index("idx_chain_name_status", "chain_name", "status"),
    )

    def __repr__(self):
        return (
            f"<ChainExecution(id={self.id}"
            ",chain_name={self.chain_name}"
            ",status={self.status})>"
        )  # noqa: E501

    def increment_completed_tasks(self):
        """완료된 작업 수 증가"""
        self.completed_tasks += 1
        # 타입 힌트 문제 해결을 위해 실제 값으로 비교
        completed = getattr(self, "completed_tasks", 0)
        total = getattr(self, "total_tasks", 0)
        if completed >= total:
            self.complete_execution(success=True)

    def increment_failed_tasks(self):
        """실패한 작업 수 증가"""
        self.failed_tasks += 1

    def start_execution(self):
        """체인 실행 시작"""
        self.status = ProcessStatus.STARTED
        self.started_at = datetime.now()

    def complete_execution(
        self,
        success: bool = True,
        final_result=None,
        error_message: Optional[str] = None,
    ):
        """체인 실행 완료"""
        self.status = ProcessStatus.SUCCESS if success else ProcessStatus.FAILURE
        self.finished_at = datetime.now()
        if final_result is not None:
            self.final_result = final_result
        if error_message:
            self.error_message = error_message
