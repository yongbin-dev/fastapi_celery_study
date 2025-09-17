# crud/task_execution_history.py

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_
from datetime import datetime, timedelta

from .base import CRUDBase
from app.models.task_execution_history import TaskExecutionHistory


class CRUDTaskExecutionHistory(CRUDBase[TaskExecutionHistory, dict, dict]):
    """TaskExecutionHistory 모델용 CRUD 클래스"""

    def get_by_task_id(
        self,
        db: Session,
        *,
        task_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskExecutionHistory]:
        """task_id로 실행 이력 목록 조회"""
        return db.query(TaskExecutionHistory).filter(
            TaskExecutionHistory.task_id == task_id
        ).order_by(desc(TaskExecutionHistory.attempt_number)).offset(skip).limit(limit).all()

    def get_by_task_id_and_attempt(
        self,
        db: Session,
        *,
        task_id: str,
        attempt_number: int
    ) -> Optional[TaskExecutionHistory]:
        """task_id와 시도 번호로 특정 실행 이력 조회"""
        return db.query(TaskExecutionHistory).filter(
            and_(
                TaskExecutionHistory.task_id == task_id,
                TaskExecutionHistory.attempt_number == attempt_number
            )
        ).first()

    def get_latest_attempt(
        self,
        db: Session,
        *,
        task_id: str
    ) -> Optional[TaskExecutionHistory]:
        """특정 작업의 최신 시도 조회"""
        return db.query(TaskExecutionHistory).filter(
            TaskExecutionHistory.task_id == task_id
        ).order_by(desc(TaskExecutionHistory.attempt_number)).first()

    def get_by_status(
        self,
        db: Session,
        *,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskExecutionHistory]:
        """상태별 실행 이력 목록 조회"""
        return db.query(TaskExecutionHistory).filter(
            TaskExecutionHistory.status == status
        ).order_by(desc(TaskExecutionHistory.created_at)).offset(skip).limit(limit).all()

    def get_failed_attempts(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskExecutionHistory]:
        """실패한 시도들 조회"""
        return db.query(TaskExecutionHistory).filter(
            TaskExecutionHistory.status.in_(['FAILURE', 'TIMEOUT'])
        ).order_by(desc(TaskExecutionHistory.created_at)).offset(skip).limit(limit).all()

    def get_with_task(
        self,
        db: Session,
        *,
        task_id: str
    ) -> List[TaskExecutionHistory]:
        """작업 로그와 함께 실행 이력 조회"""
        return db.query(TaskExecutionHistory).options(
            joinedload(TaskExecutionHistory.task)
        ).filter(TaskExecutionHistory.task_id == task_id).order_by(
            desc(TaskExecutionHistory.attempt_number)
        ).all()

    def create_attempt(
        self,
        db: Session,
        *,
        task_id: str,
        attempt_number: int,
        status: str = 'STARTED'
    ) -> TaskExecutionHistory:
        """새 시도 기록 생성"""

        execution_history = TaskExecutionHistory(
            task_id=task_id,
            attempt_number=attempt_number,
            status=status,
            started_at=datetime.now()
        )
        db.add(execution_history)
        db.commit()
        db.refresh(execution_history)
        return execution_history

    def complete_attempt(
        self,
        db: Session,
        *,
        execution_history: TaskExecutionHistory,
        status: str,
        error_message: Optional[str] = None,
        traceback: Optional[str] = None
    ) -> TaskExecutionHistory:
        """시도 완료 처리"""

        execution_history.status = status
        execution_history.completed_at = datetime.now()

        if error_message:
            execution_history.error_message = error_message
        if traceback:
            execution_history.traceback = traceback

        db.add(execution_history)
        db.commit()
        db.refresh(execution_history)
        return execution_history

    def get_retry_count(
        self,
        db: Session,
        *,
        task_id: str
    ) -> int:
        """특정 작업의 재시도 횟수 조회"""
        return db.query(TaskExecutionHistory).filter(
            TaskExecutionHistory.task_id == task_id
        ).count()

    def get_failure_patterns(
        self,
        db: Session,
        *,
        limit: int = 100
    ) -> List[dict]:
        """실패 패턴 분석"""
        from sqlalchemy import func

        result = db.query(
            func.substring(TaskExecutionHistory.error_message, 1, 100).label('error_pattern'),
            func.count(TaskExecutionHistory.id).label('count')
        ).filter(
            TaskExecutionHistory.status.in_(['FAILURE', 'TIMEOUT'])
        ).group_by(
            func.substring(TaskExecutionHistory.error_message, 1, 100)
        ).order_by(desc('count')).limit(limit).all()

        return [
            {
                'error_pattern': row.error_pattern,
                'count': row.count
            }
            for row in result
        ]

    def get_execution_stats(
        self,
        db: Session,
        *,
        task_id: Optional[str] = None
    ) -> dict:
        """실행 통계 조회"""
        from sqlalchemy import func

        query = db.query(
            func.count(TaskExecutionHistory.id).label('total_attempts'),
            func.sum(
                func.case(
                    (TaskExecutionHistory.status == 'SUCCESS', 1),
                    else_=0
                )
            ).label('success_count'),
            func.sum(
                func.case(
                    (TaskExecutionHistory.status.in_(['FAILURE', 'TIMEOUT']), 1),
                    else_=0
                )
            ).label('failure_count'),
            func.avg(
                func.case(
                    (
                        and_(
                            TaskExecutionHistory.started_at.isnot(None),
                            TaskExecutionHistory.completed_at.isnot(None)
                        ),
                        func.extract('epoch', TaskExecutionHistory.completed_at - TaskExecutionHistory.started_at)
                    ),
                    else_=None
                )
            ).label('avg_duration')
        )

        if task_id:
            query = query.filter(TaskExecutionHistory.task_id == task_id)

        result = query.first()

        total_attempts = result.total_attempts or 0
        success_count = result.success_count or 0
        failure_count = result.failure_count or 0

        return {
            'total_attempts': total_attempts,
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': round((success_count / total_attempts * 100) if total_attempts > 0 else 0, 2),
            'failure_rate': round((failure_count / total_attempts * 100) if total_attempts > 0 else 0, 2),
            'avg_duration': float(result.avg_duration or 0)
        }

    def get_recent_failures(
        self,
        db: Session,
        *,
        days: int = 7,
        limit: int = 50
    ) -> List[TaskExecutionHistory]:
        """최근 N일간 실패한 시도들 조회"""
        from datetime import datetime, timedelta

        since_date = datetime.now() - timedelta(days=days)
        return db.query(TaskExecutionHistory).filter(
            and_(
                TaskExecutionHistory.status.in_(['FAILURE', 'TIMEOUT']),
                TaskExecutionHistory.created_at >= since_date
            )
        ).order_by(desc(TaskExecutionHistory.created_at)).limit(limit).all()

    def get_long_running_attempts(
        self,
        db: Session,
        *,
        min_duration_seconds: int = 300,  # 5분
        limit: int = 50
    ) -> List[TaskExecutionHistory]:
        """장시간 실행된 시도들 조회"""
        return db.query(TaskExecutionHistory).filter(
            and_(
                TaskExecutionHistory.started_at.isnot(None),
                TaskExecutionHistory.completed_at.isnot(None),
                func.extract('epoch', TaskExecutionHistory.completed_at - TaskExecutionHistory.started_at) >= min_duration_seconds
            )
        ).order_by(
            desc(func.extract('epoch', TaskExecutionHistory.completed_at - TaskExecutionHistory.started_at))
        ).limit(limit).all()

    def cleanup_old_history(
        self,
        db: Session,
        *,
        days: int = 180
    ) -> int:
        """오래된 실행 이력 정리"""
        from datetime import datetime, timedelta

        cleanup_date = datetime.now() - timedelta(days=days)
        deleted_count = db.query(TaskExecutionHistory).filter(
            TaskExecutionHistory.created_at < cleanup_date
        ).delete()
        db.commit()
        return deleted_count

    def get_task_reliability_score(
        self,
        db: Session,
        *,
        task_id: str
    ) -> dict:
        """작업 신뢰성 점수 계산"""
        stats = self.get_execution_stats(db, task_id=task_id)

        if stats['total_attempts'] == 0:
            return {
                'reliability_score': 0,
                'grade': 'N/A',
                'total_attempts': 0
            }

        success_rate = stats['success_rate']

        # 신뢰성 등급 계산
        if success_rate >= 95:
            grade = 'A'
        elif success_rate >= 85:
            grade = 'B'
        elif success_rate >= 70:
            grade = 'C'
        elif success_rate >= 50:
            grade = 'D'
        else:
            grade = 'F'

        return {
            'reliability_score': success_rate,
            'grade': grade,
            'total_attempts': stats['total_attempts'],
            'success_count': stats['success_count'],
            'failure_count': stats['failure_count']
        }


# 인스턴스 생성
task_execution_history = CRUDTaskExecutionHistory(TaskExecutionHistory)