# models/queue_stats.py
from sqlalchemy import Column, String, Integer, Float, DateTime, Index
from datetime import datetime, timedelta
from .base import Base


class QueueStats(Base):
    """
    큐 통계 테이블
    큐별 작업 처리 통계 및 성능 메트릭
    """

    __tablename__ = "queue_stats"

    # 기본 필드
    id = Column(Integer, primary_key=True, comment="고유 식별자")
    queue_name = Column(String(255), nullable=False, index=True, comment="큐 이름")

    # 작업 통계
    pending_tasks = Column(Integer, default=0, comment="대기중인 작업 수")
    active_tasks = Column(Integer, default=0, comment="처리중인 작업 수")
    completed_tasks = Column(Integer, default=0, comment="완료된 작업 수")
    failed_tasks = Column(Integer, default=0, comment="실패한 작업 수")

    # 성능 메트릭
    avg_execution_time = Column(Float, comment="평균 실행 시간 (초)")
    max_execution_time = Column(Float, comment="최대 실행 시간 (초)")
    min_execution_time = Column(Float, comment="최소 실행 시간 (초)")

    # 추가 메트릭
    throughput = Column(Float, comment="처리량 (작업/분)")
    error_rate = Column(Float, comment="에러율 (%)")

    # 메타데이터
    measured_at = Column(
        DateTime, default=datetime.now, index=True, comment="측정 시간"
    )

    # 인덱스 정의
    __table_args__ = (
        Index("idx_queue_stats_name_time", "queue_name", "measured_at"),
        Index("idx_queue_stats_pending", "pending_tasks"),
    )

    def __repr__(self):
        return f"<QueueStats(queue={self.queue_name}, pending={self.pending_tasks}, active={self.active_tasks})>"

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            "id": self.id,
            "queue_name": self.queue_name,
            "pending_tasks": self.pending_tasks,
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "avg_execution_time": self.avg_execution_time,
            "max_execution_time": self.max_execution_time,
            "min_execution_time": self.min_execution_time,
            "throughput": self.throughput,
            "error_rate": self.error_rate,
            "measured_at": self.measured_at,
        }
