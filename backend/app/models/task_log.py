# models/task_log.py
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
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
    # args = Column(Text, comment="작업 위치 인자 (JSON 형식)")
    # kwargs = Column(Text, comment="작업 키워드 인자 (JSON 형식)")

    # 결과 및 에러
    # result = Column(Text, comment="작업 실행 결과 (JSON 형식)")
    error = Column(String(512), comment="에러 메시지")

    # 시간 추적
    started_at = Column(DateTime, index=True, comment="작업 시작 시간")
    finished_at = Column(DateTime, comment="작업 완료 시간")

    # 재시도 정보
    retries = Column(Integer, default=0, comment="재시도 횟수")

    # 체인 실행과의 관계
    chain_execution_id = Column(
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
