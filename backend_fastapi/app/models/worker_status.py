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

    @property
    def is_online(self):
        """온라인 상태 여부"""
        return self.status == "ONLINE"

    @property
    def is_busy(self):
        """바쁜 상태 여부"""
        return self.status == "BUSY" or self.active_tasks > 0

    @property
    def is_stale(self, threshold_seconds=60):
        """
        하트비트가 오래된 상태 여부

        Args:
            threshold_seconds: 임계값 (초)
        """
        if not self.last_heartbeat:
            return True

        threshold = datetime.now() - timedelta(seconds=threshold_seconds)
        return self.last_heartbeat < threshold

    @property
    def uptime(self):
        """가동 시간 (초)"""
        if not self.started_at:
            return None

        end_time = self.stopped_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    @property
    def success_rate(self):
        """성공률 (%)"""
        if self.processed_tasks == 0:
            return 0.0

        successful = self.processed_tasks - self.failed_tasks
        return (successful / self.processed_tasks) * 100

    def update_status(self):
        """상태 자동 업데이트"""
        if self.is_stale():
            self.status = "OFFLINE"
        elif self.active_tasks > 0:
            self.status = "BUSY"
        else:
            self.status = "IDLE"

    def increment_processed(self, success=True):
        """처리 카운트 증가"""
        self.processed_tasks += 1
        if not success:
            self.failed_tasks += 1

        if self.active_tasks > 0:
            self.active_tasks -= 1

    def start_task(self):
        """작업 시작"""
        self.active_tasks += 1
        self.status = "BUSY"

    def heartbeat(self):
        """하트비트 업데이트"""
        self.last_heartbeat = datetime.now()
        if self.status == "OFFLINE":
            self.status = "IDLE" if self.active_tasks == 0 else "BUSY"

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            "id": self.id,
            "worker_name": self.worker_name,
            "hostname": self.hostname,
            "pid": self.pid,
            "status": self.status,
            "is_online": self.is_online,
            "is_busy": self.is_busy,
            "is_stale": self.is_stale(),
            "active_tasks": self.active_tasks,
            "processed_tasks": self.processed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.success_rate,
            "last_heartbeat": self.last_heartbeat.isoformat()
            if self.last_heartbeat
            else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "uptime": self.uptime,
        }

    @classmethod
    def create_or_update_worker(cls, session, worker_name, hostname=None, pid=None):
        """워커 생성 또는 업데이트 헬퍼"""
        worker = session.query(cls).filter_by(worker_name=worker_name).first()

        if not worker:
            worker = cls(
                worker_name=worker_name,
                hostname=hostname or worker_name.split("@")[1]
                if "@" in worker_name
                else worker_name,
                pid=pid,
                status="ONLINE",
                started_at=datetime.now(),
                last_heartbeat=datetime.now(),
            )
            session.add(worker)
        else:
            worker.status = "ONLINE"
            worker.last_heartbeat = datetime.now()
            if hostname:
                worker.hostname = hostname
            if pid:
                worker.pid = pid

        return worker
