from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import mapped_column, relationship

from ..schemas.enums import ProcessStatus
from .base import Base


class ChainExecution(Base):
    """
    체인 실행 테이블
    Celery 체인(workflow) 실행 상태 및 결과를 추적
    """

    __tablename__ = "chain_executions"

    # 기본 필드
    id = mapped_column(Integer, primary_key=True, comment="고유 식별자")
    chain_name = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="체인 이름 (예: user_signup_workflow)",
    )

    # --- [수정됨] ForeignKey 추가 ---
    batch_id = mapped_column(
        String(255),
        ForeignKey("batch_executions.batch_id"),  # BatchExecution.batch_id 참조
        nullable=True,
        index=True,
        comment="배치 ID (배치 실행 시에만 사용)",
    )

    # 상태 관리
    status = mapped_column(
        String(20),
        default=ProcessStatus.PENDING,
        nullable=False,
        index=True,
        comment="체인 실행 상태",
    )

    # 타임스탬프
    started_at = mapped_column(DateTime, nullable=True, comment="시작 시간")
    finished_at = mapped_column(DateTime, nullable=True, comment="완료 시간")

    # 메타 정보
    initiated_by = mapped_column(
        String(100), nullable=True, comment="시작한 사용자/시스템"
    )
    input_data = mapped_column(JSON, nullable=True, comment="입력 데이터 (JSON)")
    final_result = mapped_column(JSON, nullable=True, comment="최종 결과 (JSON)")
    error_message = mapped_column(Text, nullable=True, comment="오류 메시지")

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
        return f"<ChainExecution(id={self.id},status={self.status})>"

    def start_execution(self):
        """체인 실행 시작"""
        if self.status == ProcessStatus.PENDING:
            self.status = ProcessStatus.STARTED
            self.started_at = datetime.now()

    def complete_execution(
        self,
        success: bool = True,
        final_result=None,
        error_message: Optional[str] = None,
    ):
        """체인 실행 완료"""
        # 이미 완료된 상태가 아니라면 상태 변경
        if self.status not in {ProcessStatus.SUCCESS, ProcessStatus.FAILURE}:
            self.status = ProcessStatus.SUCCESS if success else ProcessStatus.FAILURE
            self.finished_at = datetime.now()
            if final_result is not None:
                self.final_result = final_result
            if error_message and not self.error_message:
                self.error_message = error_message
