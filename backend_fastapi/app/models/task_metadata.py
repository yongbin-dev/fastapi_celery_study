# models/task_metadata.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class TaskMetadata(Base):
    """
    작업 메타데이터 테이블
    Celery 작업의 추가 정보 (워커, 큐, 라우팅 등)를 저장
    """
    __tablename__ = "task_metadata"
    
    # 기본 필드
    id = Column(Integer, primary_key=True, comment="고유 식별자")
    task_id = Column(
        String(255), 
        ForeignKey("task_logs.task_id", ondelete="CASCADE"), 
        index=True,
        nullable=False,
        comment="작업 ID (외래키)"
    )
    
    # 워커 정보
    worker_name = Column(
        String(255), 
        index=True,
        comment="워커 이름 (예: celery@worker-01)"
    )
    
    # 큐 및 라우팅 정보
    queue_name = Column(
        String(255),
        default="default",
        comment="큐 이름 (예: default, priority)"
    )
    exchange = Column(
        String(255),
        comment="Exchange 이름 (AMQP)"
    )
    routing_key = Column(
        String(255),
        comment="라우팅 키 (AMQP)"
    )
    
    # 작업 스케줄링
    priority = Column(
        Integer,
        default=0,
        comment="작업 우선순위 (0-9, 높을수록 우선)"
    )
    eta = Column(
        DateTime,
        comment="예정 실행 시간 (ETA: Estimated Time of Arrival)"
    )
    expires = Column(
        DateTime,
        comment="작업 만료 시간"
    )
    
    # 작업 체인/그룹 정보
    parent_id = Column(
        String(255),
        comment="부모 작업 ID (체인/그룹)"
    )
    root_id = Column(
        String(255),
        comment="루트 작업 ID (워크플로우)"
    )
    
    
    # 관계 설정
    task = relationship("TaskLog", back_populates="task_metadata")
    
    # 인덱스 정의
    __table_args__ = (
        Index('idx_metadata_worker_queue', 'worker_name', 'queue_name'),
        Index('idx_metadata_parent_root', 'parent_id', 'root_id'),
    )
    
    def __repr__(self):
        return f"<TaskMetadata(task_id={self.task_id}, worker={self.worker_name}, queue={self.queue_name})>"
    
    @property
    def is_scheduled(self):
        """예약된 작업 여부"""
        return self.eta is not None and self.eta > datetime.now()
    
    @property
    def is_expired(self):
        """만료된 작업 여부"""
        return self.expires is not None and self.expires < datetime.now()
    
    @property
    def is_child_task(self):
        """자식 작업 여부"""
        return self.parent_id is not None
    
    @property
    def is_part_of_workflow(self):
        """워크플로우 일부 여부"""
        return self.root_id is not None
    
    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'worker_name': self.worker_name,
            'queue_name': self.queue_name,
            'exchange': self.exchange,
            'routing_key': self.routing_key,
            'priority': self.priority,
            'eta': self.eta.isoformat() if self.eta else None,
            'expires': self.expires.isoformat() if self.expires else None,
            'parent_id': self.parent_id,
            'root_id': self.root_id,
            'is_scheduled': self.is_scheduled,
            'is_expired': self.is_expired,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }