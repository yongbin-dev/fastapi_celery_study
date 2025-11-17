# crud/task_log.py

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from shared.models.task_log import TaskLog
from shared.schemas.task_log import TaskLogCreate, TaskLogUpdate

from .base import CRUDBase


class CRUDTaskLog(CRUDBase[TaskLog, TaskLogCreate, TaskLogUpdate]):  # type: ignore
    """TaskLog 모델용 CRUD 클래스"""

    def get_by_celery_task_id(
        self, db: Session, *, celery_task_id: str
    ) -> Optional[TaskLog]:
        """Celery task_id로 작업 로그 조회"""
        return (
            db.query(TaskLog)
            .filter(TaskLog.celery_task_id == celery_task_id)
            .first()
        )

    def create_task_log(
        self,
        db: Session,
        *,
        celery_task_id: str,
        task_name: str,
        status: str = "PENDING",
        chain_execution_id: Optional[int] = None,
    ) -> TaskLog:
        """새 작업 로그 생성"""
        task_log = TaskLog(
            celery_task_id=celery_task_id,
            task_name=task_name,
            status=status,
            chain_execution_id=chain_execution_id,
            started_at=datetime.now(),
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
        error: Optional[str] = None,
    ) -> TaskLog:
        """작업 상태 업데이트"""
        task_log.status = status  # type: ignore
        if error is not None:
            task_log.error = error  # type: ignore

        # 완료 시간 설정
        if status in ["SUCCESS", "FAILURE", "REVOKED"] and task_log.finished_at is None:
            task_log.finished_at = datetime.now()  # type: ignore

        db.add(task_log)
        db.commit()
        db.refresh(task_log)
        return task_log


# # 인스턴스 생성
task_log_crud = CRUDTaskLog(TaskLog)
