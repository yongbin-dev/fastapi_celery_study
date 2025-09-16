# crud/task_result.py

from typing import List, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_

from .base import CRUDBase
from ...models.task_result import TaskResult


class CRUDTaskResult(CRUDBase[TaskResult, dict, dict]):
    """TaskResult 모델용 CRUD 클래스"""

    def get_by_task_id(self, db: Session, *, task_id: str) -> Optional[TaskResult]:
        """task_id로 작업 결과 조회"""
        return db.query(TaskResult).filter(
            TaskResult.task_id == task_id
        ).first()

    def get_by_result_type(
        self,
        db: Session,
        *,
        result_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskResult]:
        """결과 타입별 작업 결과 목록 조회"""
        return db.query(TaskResult).filter(
            TaskResult.result_type == result_type
        ).order_by(desc(TaskResult.created_at)).offset(skip).limit(limit).all()

    def get_large_results(
        self,
        db: Session,
        *,
        min_size: int = 1024 * 1024,  # 1MB
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskResult]:
        """대용량 결과 목록 조회"""
        return db.query(TaskResult).filter(
            TaskResult.result_size >= min_size
        ).order_by(desc(TaskResult.result_size)).offset(skip).limit(limit).all()

    def get_with_task(
        self,
        db: Session,
        *,
        task_id: str
    ) -> Optional[TaskResult]:
        """작업 로그와 함께 결과 조회"""
        return db.query(TaskResult).options(
            joinedload(TaskResult.task)
        ).filter(TaskResult.task_id == task_id).first()

    def create_task_result(
        self,
        db: Session,
        *,
        task_id: str,
        data: Any,
        result_type: str = 'auto'
    ) -> TaskResult:
        """새 작업 결과 생성"""
        task_result = TaskResult(task_id=task_id)
        task_result.set_result(data, result_type)

        db.add(task_result)
        db.commit()
        db.refresh(task_result)
        return task_result

    def update_result(
        self,
        db: Session,
        *,
        task_result: TaskResult,
        data: Any,
        result_type: str = 'auto'
    ) -> TaskResult:
        """작업 결과 업데이트"""
        task_result.set_result(data, result_type)

        db.add(task_result)
        db.commit()
        db.refresh(task_result)
        return task_result

    def get_result_data(
        self,
        db: Session,
        *,
        task_id: str
    ) -> Optional[Any]:
        """작업 결과 데이터 조회"""
        task_result = self.get_by_task_id(db, task_id=task_id)
        if task_result:
            return task_result.get_result()
        return None

    def get_result_preview(
        self,
        db: Session,
        *,
        task_id: str,
        max_length: int = 100
    ) -> Optional[str]:
        """작업 결과 미리보기 조회"""
        task_result = self.get_by_task_id(db, task_id=task_id)
        if task_result:
            return task_result.get_result_preview(max_length)
        return None

    def get_recent_results(
        self,
        db: Session,
        *,
        days: int = 7,
        limit: int = 100
    ) -> List[TaskResult]:
        """최근 N일간 작업 결과 목록 조회"""
        from datetime import datetime, timedelta

        since_date = datetime.utcnow() - timedelta(days=days)
        return db.query(TaskResult).filter(
            TaskResult.created_at >= since_date
        ).order_by(desc(TaskResult.created_at)).limit(limit).all()

    def get_stats_by_type(self, db: Session) -> dict:
        """결과 타입별 통계 조회"""
        from sqlalchemy import func

        result = db.query(
            TaskResult.result_type,
            func.count(TaskResult.id).label('count'),
            func.avg(TaskResult.result_size).label('avg_size'),
            func.sum(TaskResult.result_size).label('total_size')
        ).group_by(TaskResult.result_type).all()

        stats = {}
        for row in result:
            stats[row.result_type] = {
                'count': row.count,
                'avg_size': float(row.avg_size or 0),
                'total_size': int(row.total_size or 0)
            }
        return stats

    def cleanup_old_results(
        self,
        db: Session,
        *,
        days: int = 90
    ) -> int:
        """오래된 결과 정리"""
        from datetime import datetime, timedelta

        cleanup_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = db.query(TaskResult).filter(
            TaskResult.created_at < cleanup_date
        ).delete()
        db.commit()
        return deleted_count

    def cleanup_large_results(
        self,
        db: Session,
        *,
        max_size: int = 100 * 1024 * 1024,  # 100MB
        days: int = 30
    ) -> int:
        """대용량 오래된 결과 정리"""
        from datetime import datetime, timedelta

        cleanup_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = db.query(TaskResult).filter(
            and_(
                TaskResult.result_size >= max_size,
                TaskResult.created_at < cleanup_date
            )
        ).delete()
        db.commit()
        return deleted_count

    def get_total_storage_usage(self, db: Session) -> dict:
        """전체 저장소 사용량 조회"""
        from sqlalchemy import func

        result = db.query(
            func.count(TaskResult.id).label('total_count'),
            func.sum(TaskResult.result_size).label('total_size'),
            func.avg(TaskResult.result_size).label('avg_size'),
            func.max(TaskResult.result_size).label('max_size')
        ).first()

        return {
            'total_count': result.total_count or 0,
            'total_size': int(result.total_size or 0),
            'avg_size': float(result.avg_size or 0),
            'max_size': int(result.max_size or 0)
        }

    def get_results_by_task_name(
        self,
        db: Session,
        *,
        task_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskResult]:
        """작업명별 결과 목록 조회 (작업 로그와 조인)"""
        from ...models.task_log import TaskLog

        return db.query(TaskResult).join(TaskLog).filter(
            TaskLog.task_name == task_name
        ).order_by(desc(TaskResult.created_at)).offset(skip).limit(limit).all()


# 인스턴스 생성
task_result = CRUDTaskResult(TaskResult)