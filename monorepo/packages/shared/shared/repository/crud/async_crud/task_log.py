# crud/async_crud/task_log.py

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.task_log import TaskLog
from shared.schemas.task_log import TaskLogCreate, TaskLogUpdate

from .base import AsyncCRUDBase


class AsyncCRUDTaskLog(AsyncCRUDBase[TaskLog, TaskLogCreate, TaskLogUpdate]):
    """TaskLog 모델용 비동기 CRUD 클래스"""

    async def get_by_id(self, db: AsyncSession, *, id: str) -> Optional[TaskLog]:
        """id 작업 로그 조회"""
        try:
            stmt = select(TaskLog).where(TaskLog.id == id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise e


# 인스턴스 생성
task_log_crud = AsyncCRUDTaskLog(TaskLog)
