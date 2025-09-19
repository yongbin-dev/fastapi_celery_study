# models/worker_status.py
from sqlalchemy import Column, String, Integer, DateTime, Index
from datetime import datetime, timedelta
from .base import Base


class WorkerStatus(Base):
    """
    워커 상태 테이블
    Celery 워커의 상태 및 통계 추적
    """

    __tablename__ = "worker_status"

    # 기본 필드
    id = Column(Integer, primary_key=True, comment="고유 식별자")
    worker_name = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="워커 이름 (celery@hostname)",
    )

    # 시스템 정보
    hostname = Column(String(255), comment="호스트명")
    pid = Column(Integer, comment="프로세스 ID")

    # 상태 정보
    status = Column(
        String(50),
        default="OFFLINE",
        index=True,
        comment="워커 상태 (ONLINE/OFFLINE/BUSY/IDLE)",
    )

    # 작업 통계
    active_tasks = Column(Integer, default=0, comment="현재 처리중인 작업 수")
    processed_tasks = Column(Integer, default=0, comment="총 처리한 작업 수")
    failed_tasks = Column(Integer, default=0, comment="실패한 작업 수")

    # 시간 추적
    last_heartbeat = Column(DateTime, comment="마지막 하트비트 시간")
    started_at = Column(DateTime, comment="워커 시작 시간")
    stopped_at = Column(DateTime, comment="워커 종료 시간")

    # 인덱스 정의
    __table_args__ = (
        Index("idx_worker_status_heartbeat", "last_heartbeat"),
        Index("idx_worker_status_active", "status", "active_tasks"),
    )

    def __repr__(self):
        return f"<WorkerStatus(name={self.worker_name}, status={self.status}, active={self.active_tasks})>"
