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
    queue_name = Column(
        String(255), 
        nullable=False,
        index=True,
        comment="큐 이름"
    )
    
    # 작업 통계
    pending_tasks = Column(
        Integer, 
        default=0,
        comment="대기중인 작업 수"
    )
    active_tasks = Column(
        Integer, 
        default=0,
        comment="처리중인 작업 수"
    )
    completed_tasks = Column(
        Integer, 
        default=0,
        comment="완료된 작업 수"
    )
    failed_tasks = Column(
        Integer, 
        default=0,
        comment="실패한 작업 수"
    )
    
    # 성능 메트릭
    avg_execution_time = Column(
        Float,
        comment="평균 실행 시간 (초)"
    )
    max_execution_time = Column(
        Float,
        comment="최대 실행 시간 (초)"
    )
    min_execution_time = Column(
        Float,
        comment="최소 실행 시간 (초)"
    )
    
    # 추가 메트릭
    throughput = Column(
        Float,
        comment="처리량 (작업/분)"
    )
    error_rate = Column(
        Float,
        comment="에러율 (%)"
    )
    
    # 메타데이터
    measured_at = Column(
        DateTime, 
        default=datetime.now,
        index=True,
        comment="측정 시간"
    )
    
    # 인덱스 정의
    __table_args__ = (
        Index('idx_queue_stats_name_time', 'queue_name', 'measured_at'),
        Index('idx_queue_stats_pending', 'pending_tasks'),
    )
    
    def __repr__(self):
        return f"<QueueStats(queue={self.queue_name}, pending={self.pending_tasks}, active={self.active_tasks})>"
    
    @property
    def total_tasks(self):
        """전체 작업 수"""
        return self.pending_tasks + self.active_tasks + self.completed_tasks + self.failed_tasks
    
    @property
    def success_rate(self):
        """성공률 (%)"""
        total_finished = self.completed_tasks + self.failed_tasks
        if total_finished == 0:
            return 0.0
        return (self.completed_tasks / total_finished) * 100
    
    @property
    def is_congested(self, threshold=100):
        """
        큐 혼잡 여부
        
        Args:
            threshold: 대기 작업 임계값
        """
        return self.pending_tasks > threshold
    
    @property
    def health_score(self):
        """
        큐 건강도 점수 (0-100)
        성공률, 처리 속도, 대기 작업 수를 종합 평가
        """
        score = 100.0
        
        # 성공률 반영 (40%)
        score -= (100 - self.success_rate) * 0.4
        
        # 대기 작업 반영 (30%)
        if self.pending_tasks > 1000:
            score -= 30
        elif self.pending_tasks > 500:
            score -= 20
        elif self.pending_tasks > 100:
            score -= 10
        
        # 에러율 반영 (30%)
        if self.error_rate:
            score -= min(self.error_rate * 3, 30)
        
        return max(0, score)
    
    def calculate_metrics(self, tasks_data):
        """
        작업 데이터로부터 메트릭 계산
        
        Args:
            tasks_data: 작업 데이터 리스트
        """
        if not tasks_data:
            return
        
        execution_times = []
        completed = 0
        failed = 0
        
        for task in tasks_data:
            if task.get('status') == 'SUCCESS':
                completed += 1
                if task.get('duration'):
                    execution_times.append(task['duration'])
            elif task.get('status') == 'FAILURE':
                failed += 1
        
        self.completed_tasks = completed
        self.failed_tasks = failed
        
        if execution_times:
            self.avg_execution_time = sum(execution_times) / len(execution_times)
            self.max_execution_time = max(execution_times)
            self.min_execution_time = min(execution_times)
        
        # 처리량 계산 (작업/분)
        if self.completed_tasks > 0 and self.avg_execution_time:
            self.throughput = 60.0 / self.avg_execution_time
        
        # 에러율 계산
        total = completed + failed
        if total > 0:
            self.error_rate = (failed / total) * 100
    
    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'id': self.id,
            'queue_name': self.queue_name,
            'pending_tasks': self.pending_tasks,
            'active_tasks': self.active_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'total_tasks': self.total_tasks,
            'avg_execution_time': self.avg_execution_time,
            'max_execution_time': self.max_execution_time,
            'min_execution_time': self.min_execution_time,
            'throughput': self.throughput,
            'error_rate': self.error_rate,
            'success_rate': self.success_rate,
            'is_congested': self.is_congested(),
            'health_score': self.health_score,
            'measured_at': self.measured_at.isoformat() if self.measured_at else None
        }
    
    @classmethod
    def get_latest_stats(cls, session, queue_name, hours=1):
        """
        최근 통계 조회
        
        Args:
            session: DB 세션
            queue_name: 큐 이름
            hours: 조회 시간 범위
        """
        since = datetime.now() - timedelta(hours=hours)
        
        return session.query(cls).filter(
            cls.queue_name == queue_name,
            cls.measured_at >= since
        ).order_by(cls.measured_at.desc()).all()
    
    @classmethod
    def aggregate_stats(cls, stats_list):
        """
        여러 통계 집계
        
        Args:
            stats_list: QueueStats 리스트
            
        Returns:
            집계된 통계 딕셔너리
        """
        if not stats_list:
            return None
        
        return {
            'queue_name': stats_list[0].queue_name,
            'avg_pending': sum(s.pending_tasks for s in stats_list) / len(stats_list),
            'avg_active': sum(s.active_tasks for s in stats_list) / len(stats_list),
            'total_completed': sum(s.completed_tasks for s in stats_list),
            'total_failed': sum(s.failed_tasks for s in stats_list),
            'avg_execution_time': sum(s.avg_execution_time or 0 for s in stats_list) / len(stats_list),
            'avg_throughput': sum(s.throughput or 0 for s in stats_list) / len(stats_list),
            'avg_error_rate': sum(s.error_rate or 0 for s in stats_list) / len(stats_list),
            'period_start': min(s.measured_at for s in stats_list),
            'period_end': max(s.measured_at for s in stats_list)
        }