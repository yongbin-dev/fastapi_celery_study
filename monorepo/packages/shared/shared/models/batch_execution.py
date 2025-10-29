from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..schemas.enums import ProcessStatus
from .base import Base


class BatchExecution(Base):
    """
    배치 실행 테이블
    대량 이미지 배치 처리 상태 및 결과를 추적
    """

    __tablename__ = "batch_executions"

    # 기본 필드
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="고유 식별자")
    batch_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True, comment="배치 고유 ID"
    )
    batch_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="배치 이름",
    )

    # 상태 관리
    status = mapped_column(
        String(20),
        default=ProcessStatus.PENDING,
        nullable=False,
        index=True,
        comment="배치 실행 상태",
    )

    # 이미지 통계
    total_images: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="총 이미지 수"
    )
    completed_images: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="완료된 이미지 수"
    )
    failed_images: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="실패한 이미지 수"
    )

    # 청크 통계
    total_chunks: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="총 청크 수"
    )
    completed_chunks: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="완료된 청크 수"
    )
    failed_chunks: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="실패한 청크 수"
    )

    # 청크 크기 설정
    chunk_size: Mapped[int] = mapped_column(
        Integer, default=10, nullable=False, comment="청크당 이미지 수"
    )

    # 타임스탬프
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, comment="시작 시간"
    )
    finished_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, comment="완료 시간"
    )

    # 메타 정보
    initiated_by: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="시작한 사용자/시스템"
    )
    input_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="입력 데이터 (이미지 경로 등)"
    )
    options: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="파이프라인 옵션"
    )
    final_result: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="최종 결과 (JSON)"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="오류 메시지"
    )
    # 관계 정의 - ChainExecution과 1:N 관계
    chain_executions = relationship(
        "ChainExecution",
        backref="batch_execution",
        foreign_keys="[ChainExecution.batch_id]",
        primaryjoin="BatchExecution.batch_id == foreign(ChainExecution.batch_id)",
        cascade="all, delete-orphan",
    )

    # 인덱스 정의
    __table_args__ = (
        Index("idx_batch_status_started", "status", "started_at"),
        Index("idx_batch_name_status", "batch_name", "status"),
    )

    def __repr__(self):
        return (
            f"<BatchExecution(id={self.id}"
            f",batch_id={self.batch_id}"
            f",status={self.status}"
            f",progress={self.completed_images}/{self.total_images})>"
        )

    def _check_and_complete_execution(self):
        """
        처리된 이미지(완료+실패)가 총 이미지 수에 도달했는지 확인하고
        필요시 배치를 완료(SUCCESS 또는 FAILURE) 처리합니다.
        """
        # 이미 완료된 상태(SUCCESS, FAILURE)라면 중복 실행 방지
        if self.status in {ProcessStatus.SUCCESS, ProcessStatus.FAILURE}:
            return

        total_processed = self.completed_images + self.failed_images
        total_images = self.total_images

        # 총 처리 수가 총 이미지 수보다 크거나 같으면 완료 처리
        if total_images > 0 and total_processed >= total_images:
            # 실패한 이미지가 하나라도 있으면 배치 상태는 'FAILURE'
            success = self.failed_images == 0
            self.complete_execution(
                success=success,
                error_message="Batch completed with failures." if not success else None,
            )

    def increment_completed_images(self, count: int = 1):
        """완료된 이미지 수 증가 및 완료 상태 확인"""
        self.completed_images += count
        self._check_and_complete_execution()

    def increment_failed_images(self, count: int = 1):
        """실패한 이미지 수 증가 및 완료 상태 확인"""
        self.failed_images += count
        self._check_and_complete_execution()

    def increment_completed_chunks(self, count: int = 1):
        """완료된 청크 수 증가"""
        self.completed_chunks += count

    def increment_failed_chunks(self, count: int = 1):
        """실패한 청크 수 증가"""
        self.failed_chunks += count

    def start_execution(self):
        """배치 실행 시작"""
        if self.status == ProcessStatus.PENDING:
            self.status = ProcessStatus.STARTED
            self.started_at = datetime.now()

    def complete_execution(
        self,
        success: bool = True,
        final_result: Optional[dict] = None,
        error_message: Optional[str] = None,
    ):
        """배치 실행 완료"""
        # 이미 완료된 상태가 아니라면 상태 변경
        if self.status not in {ProcessStatus.SUCCESS, ProcessStatus.FAILURE}:
            self.status = ProcessStatus.SUCCESS if success else ProcessStatus.FAILURE
            self.finished_at = datetime.now()
            if final_result is not None:
                self.final_result = final_result
            if error_message and not self.error_message:
                # 기존 오류 메시지가 없다면 기록
                self.error_message = error_message

    def get_progress_percentage(self) -> float:
        """진행률 계산 (0-100)"""
        if self.total_images == 0:
            return 0.0
        return (self.completed_images / self.total_images) * 100
