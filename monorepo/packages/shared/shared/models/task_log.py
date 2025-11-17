# models/task_log.py
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import mapped_column, relationship

from .base import Base


class TaskLog(Base):
    """
    작업 로그 메인 테이블
    Celery 작업의 전체 생명주기를 추적
    """

    __tablename__ = "task_logs"

    # 기본 필드
    id = mapped_column(Integer, primary_key=True, comment="고유 식별자")
    celery_task_id = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Celery Task UUID",
    )
    task_name = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="작업 함수명 (예: app.tasks.send_email)",
    )
    status = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="작업 상태 (PENDING/STARTED/SUCCESS/FAILURE/RETRY/REVOKED)",
    )

    # 작업 파라미터
    # args = mapped_column(Text, comment="작업 위치 인자 (JSON 형식)")
    # kwargs = mapped_column(Text, comment="작업 키워드 인자 (JSON 형식)")

    # 결과 및 에러
    # result = mapped_column(Text, comment="작업 실행 결과 (JSON 형식)")
    error = mapped_column(String(512), comment="에러 메시지")

    # 시간 추적
    started_at = mapped_column(DateTime, index=True, comment="작업 시작 시간")
    finished_at = mapped_column(DateTime, comment="작업 완료 시간")

    # 재시도 정보
    retries = mapped_column(Integer, default=0, comment="재시도 횟수")

    # 체인 실행과의 관계
    chain_execution_id = mapped_column(
        Integer,
        ForeignKey("chain_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="소속된 체인 실행 ID",
    )

    # 관계 정의
    chain_execution = relationship(
        "ChainExecution",
        back_populates="task_logs",
        foreign_keys=[chain_execution_id],
    )

    # 인덱스 정의
    __table_args__ = (
        Index("idx_task_logs_name_status", "task_name", "status"),
        Index("idx_task_logs_started_at_desc", started_at.desc()),
        Index("idx_task_logs_chain_execution", "chain_execution_id", "status"),
    )
