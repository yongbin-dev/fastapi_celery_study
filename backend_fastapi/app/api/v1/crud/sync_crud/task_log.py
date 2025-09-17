# crud/task_log.py

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_

from .base import CRUDBase
from ...models.task_log import TaskLog
from ...schemas.enums import ProcessStatus


class CRUDTaskLog(CRUDBase[TaskLog, dict, dict]):
    """TaskLog 모델용 CRUD 클래스"""

    def get_by_task_id(self, db: Session, *, task_id: str) -> Optional[TaskLog]:
        """task_id로 작업 로그 조회"""
        return db.query(TaskLog).filter(
            TaskLog.task_id == task_id
        ).first()

    def get_by_task_name(
        self,
        db: Session,
        *,
        task_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskLog]:
        """task_name으로 작업 로그 목록 조회"""
        return db.query(TaskLog).filter(
            TaskLog.task_name == task_name
        ).order_by(desc(TaskLog.created_at)).offset(skip).limit(limit).all()

    def get_by_status(
        self,
        db: Session,
        *,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskLog]:
        """상태별 작업 로그 목록 조회"""
        return db.query(TaskLog).filter(
            TaskLog.status == status
        ).order_by(desc(TaskLog.created_at)).offset(skip).limit(limit).all()

    def get_running_tasks(self, db: Session) -> List[TaskLog]:
        """실행 중인 작업 목록 조회"""
        return db.query(TaskLog).filter(
            TaskLog.status == 'STARTED'
        ).order_by(desc(TaskLog.started_at)).all()

    def get_failed_tasks(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskLog]:
        """실패한 작업 목록 조회"""
        return db.query(TaskLog).filter(
            TaskLog.status == 'FAILURE'
        ).order_by(desc(TaskLog.created_at)).offset(skip).limit(limit).all()

    def get_completed_tasks(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskLog]:
        """완료된 작업 목록 조회"""
        return db.query(TaskLog).filter(
            TaskLog.status.in_(['SUCCESS', 'FAILURE', 'REVOKED'])
        ).order_by(desc(TaskLog.completed_at)).offset(skip).limit(limit).all()

    def get_with_metadata(
        self,
        db: Session,
        *,
        task_id: str
    ) -> Optional[TaskLog]:
        """메타데이터와 함께 작업 로그 조회"""
        return db.query(TaskLog).options(
            joinedload(TaskLog.task_metadata)
        ).filter(TaskLog.task_id == task_id).first()

    def get_with_relations(
        self,
        db: Session,
        *,
        task_id: str
    ) -> Optional[TaskLog]:
        """모든 관련 데이터와 함께 작업 로그 조회"""
        return db.query(TaskLog).options(
            joinedload(TaskLog.task_metadata),
            joinedload(TaskLog.execution_history),
            joinedload(TaskLog.task_result),
            joinedload(TaskLog.dependencies),
            joinedload(TaskLog.dependents)
        ).filter(TaskLog.task_id == task_id).first()

    def create_task_log(
        self,
        db: Session,
        *,
        task_id: str,
        task_name: str,
        status: str = 'PENDING',
        args: Optional[str] = None,
        kwargs: Optional[str] = None
    ) -> TaskLog:
        """새 작업 로그 생성"""
        task_log = TaskLog(
            task_id=task_id,
            task_name=task_name,
            status=status,
            args=args,
            kwargs=kwargs
        )
        db.add(task_log)
        db.commit()
        db.refresh(task_log)
        return task_log

    def update_status(
        self,
        db: Session,
        *,
        task_log: TaskLog,
        status: str,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> TaskLog:
        """작업 상태 업데이트"""
        task_log.status = status
        if result is not None:
            task_log.result = result
        if error is not None:
            task_log.error = error

        # 시작 시간 설정
        if status == 'STARTED' and not task_log.started_at:
            
            task_log.started_at = datetime.now()

        # 완료 시간 설정
        if status in ['SUCCESS', 'FAILURE', 'REVOKED'] and not task_log.completed_at:
            
            task_log.completed_at = datetime.now()

        db.add(task_log)
        db.commit()
        db.refresh(task_log)
        return task_log

    def increment_retries(
        self,
        db: Session,
        *,
        task_log: TaskLog
    ) -> TaskLog:
        """재시도 횟수 증가"""
        task_log.retries += 1
        db.add(task_log)
        db.commit()
        db.refresh(task_log)
        return task_log

    def get_by_chain_tasks(
        self,
        db: Session,
        *,
        chain_id: str
    ) -> List[TaskLog]:
        """특정 체인의 모든 작업 로그 조회 (순서대로)"""
        # pipeline 작업들만 필터링 (app.tasks.stage로 시작하는 것들)
        return db.query(TaskLog).filter(
            TaskLog.task_name.like('app.tasks.stage%')
        ).order_by(TaskLog.task_name).all()

    def get_pipeline_tasks_by_chain(
        self,
        db: Session,
        *,
        chain_id: str
    ) -> List[TaskLog]:
        """파이프라인 작업들을 단계순으로 조회"""
        stage_tasks = []
        for stage_num in range(1, 5):  # stage1~4
            task_name = f"app.tasks.stage{stage_num}_*"
            tasks = db.query(TaskLog).filter(
                TaskLog.task_name.like(f"app.tasks.stage{stage_num}_%")
            ).order_by(desc(TaskLog.created_at)).first()
            if tasks:
                stage_tasks.append(tasks)
        return stage_tasks

    def get_recent_tasks(
        self,
        db: Session,
        *,
        days: int = 7,
        limit: int = 100
    ) -> List[TaskLog]:
        """최근 N일간 작업 로그 목록 조회"""
        from datetime import timedelta
        

        since_date = datetime.now() - timedelta(days=days)
        return db.query(TaskLog).filter(
            TaskLog.created_at >= since_date
        ).order_by(desc(TaskLog.created_at)).limit(limit).all()

    def get_stats_by_status(self, db: Session) -> dict:
        """상태별 통계 조회"""
        statuses = ['PENDING', 'STARTED', 'SUCCESS', 'FAILURE', 'RETRY', 'REVOKED']
        stats = {}
        for status in statuses:
            count = db.query(TaskLog).filter(
                TaskLog.status == status
            ).count()
            stats[status] = count
        return stats

    def get_task_performance_stats(self, db: Session, *, task_name: str) -> dict:
        """특정 작업의 성능 통계"""
        from sqlalchemy import func

        # 성공한 작업들의 실행 시간 통계
        result = db.query(
            func.count(TaskLog.id).label('total_count'),
            func.avg(
                func.extract('epoch', TaskLog.completed_at - TaskLog.started_at)
            ).label('avg_duration'),
            func.min(
                func.extract('epoch', TaskLog.completed_at - TaskLog.started_at)
            ).label('min_duration'),
            func.max(
                func.extract('epoch', TaskLog.completed_at - TaskLog.started_at)
            ).label('max_duration')
        ).filter(
            and_(
                TaskLog.task_name == task_name,
                TaskLog.status == 'SUCCESS',
                TaskLog.started_at.isnot(None),
                TaskLog.completed_at.isnot(None)
            )
        ).first()

        return {
            'total_count': result.total_count or 0,
            'avg_duration': float(result.avg_duration or 0),
            'min_duration': float(result.min_duration or 0),
            'max_duration': float(result.max_duration or 0)
        }

    def cleanup_old_logs(
        self,
        db: Session,
        *,
        days: int = 90
    ) -> int:
        """오래된 완료 로그 정리"""
        from datetime import timedelta
        

        cleanup_date = datetime.now() - timedelta(days=days)
        deleted_count = db.query(TaskLog).filter(
            and_(
                TaskLog.completed_at < cleanup_date,
                TaskLog.status.in_(['SUCCESS', 'FAILURE', 'REVOKED'])
            )
        ).delete()
        db.commit()
        return deleted_count


# 인스턴스 생성
task_log = CRUDTaskLog(TaskLog)