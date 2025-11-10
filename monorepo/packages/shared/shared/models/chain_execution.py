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
    chain_id = mapped_column(
        String(255), nullable=True, index=True, comment="체인 고유 ID"
    )
    celery_task_id = mapped_column(
        String(255), nullable=True, index=True, comment="Celery Task ID (첫 번째 task)"
    )
    chain_name = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="체인 이름 (예: user_signup_workflow)",
    )

    # --- [수정됨] ForeignKey 추가 ---
    batch_id = mapped_column(
        String(255),
        ForeignKey("batch_executions.batch_id"), # BatchExecution.batch_id 참조
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

    # 작업 통계
    total_tasks = mapped_column(
        Integer, default=0, nullable=False, comment="체인 내 총 작업 수"
    )
    completed_tasks = mapped_column(
        Integer, default=0, nullable=False, comment="완료된 작업 수"
    )
    failed_tasks = mapped_column(
        Integer, default=0, nullable=False, comment="실패한 작업 수")

    # 타임스탬프
    started_at = mapped_column(DateTime, nullable=True, comment="시작 시간")
    finished_at = mapped_column(DateTime, nullable=True, comment="완료 시간")

    # 메타 정보
    initiated_by = mapped_column(
        String(100), nullable=True, comment="시작한 사용자/시스템")
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
        return (
            f"<ChainExecution(id={self.id}"
            f",chain_id={self.chain_id}"
            f",status={self.status})>"
        )

    # --- [신규] 자동 완료 체크 메서드 ---
    def _check_and_complete_execution(self):
        """
        처리된 작업(완료+실패)이 총 작업 수에 도달했는지 확인하고
        필요시 체인을 완료(SUCCESS 또는 FAILURE) 처리합니다.
        """
        # 이미 완료된 상태라면 중복 실행 방지
        if self.status in {ProcessStatus.SUCCESS, ProcessStatus.FAILURE}:
            return

        total_processed = self.completed_tasks + self.failed_tasks
        total_tasks = self.total_tasks

        if total_tasks > 0 and total_processed >= total_tasks:
            # 실패한 작업이 하나라도 있으면 체인 상태는 'FAILURE'
            success = self.failed_tasks == 0
            self.complete_execution(
                success=success,
                error_message="Chain completed with failed tasks."
                if not success
                else None,
            )

    def increment_completed_tasks(self, count: int = 1):
        """완료된 작업 수 증가 및 완료 상태 확인"""
        self.completed_tasks += count
        self._check_and_complete_execution()

    def increment_failed_tasks(self, count: int = 1):
        """실패한 작업 수 증가 및 완료 상태 확인"""
        self.failed_tasks += count
        self._check_and_complete_execution()

    def start_execution(self):
        """체인 실행 시작"""
        if self.status == ProcessStatus.PENDING:
            self.status = ProcessStatus.STARTED
            self.started_at = datetime.now()

    # --- [수정됨] 상태 확인 가드 추가 ---
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
