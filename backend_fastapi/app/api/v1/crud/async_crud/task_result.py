# crud/async_crud/task_result.py

from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from sqlalchemy.orm import joinedload
from datetime import timedelta , datetime


from .base import AsyncCRUDBase
from ...models.task_result import TaskResult


class AsyncCRUDTaskResult(AsyncCRUDBase[TaskResult, dict, dict]):
    """TaskResult 모델용 비동기 CRUD 클래스"""

    async def get_by_task_id(self, db: AsyncSession, *, task_id: str) -> Optional[TaskResult]:
        """task_id로 작업 결과 조회"""
        try:
            stmt = select(TaskResult).where(TaskResult.task_id == task_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_result_type(
        self,
        db: AsyncSession,
        *,
        result_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskResult]:
        """결과 타입별 작업 결과 목록 조회"""
        try:
            stmt = select(TaskResult).where(
                TaskResult.result_type == result_type
            ).order_by(desc(TaskResult.created_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_large_results(
        self,
        db: AsyncSession,
        *,
        min_size: int = 1024 * 1024,  # 1MB
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskResult]:
        """대용량 결과 목록 조회"""

        stmt = select(TaskResult).where(
            TaskResult.result_size >= min_size
        ).order_by(desc(TaskResult.result_size)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())


    async def get_with_task(
        self,
        db: AsyncSession,
        *,
        task_id: str
    ) -> Optional[TaskResult]:
        """작업 로그와 함께 결과 조회"""

        stmt = select(TaskResult).options(
            joinedload(TaskResult.task)
        ).where(TaskResult.task_id == task_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


    async def create_task_result(
        self,
        db: AsyncSession,
        *,
        task_id: str,
        data: Any,
        result_type: str = 'auto'
    ) -> TaskResult:
        """새 작업 결과 생성"""

        task_result = TaskResult(task_id=task_id)
        task_result.set_result(data, result_type)

        db.add(task_result)
        await db.commit()
        await db.refresh(task_result)
        return task_result


    async def update_result(
        self,
        db: AsyncSession,
        *,
        task_result: TaskResult,
        data: Any,
        result_type: str = 'auto'
    ) -> TaskResult:
        """작업 결과 업데이트"""

        task_result.set_result(data, result_type)

        db.add(task_result)
        await db.commit()
        await db.refresh(task_result)
        return task_result

    async def get_result_data(
        self,
        db: AsyncSession,
        *,
        task_id: str
    ) -> Optional[Any]:
        """작업 결과 데이터 조회"""
        task_result = await self.get_by_task_id(db, task_id=task_id)
        if task_result:
            return task_result.get_result()
        return None

    async def get_result_preview(
        self,
        db: AsyncSession,
        *,
        task_id: str,
        max_length: int = 100
    ) -> Optional[str]:
        """작업 결과 미리보기 조회"""
        task_result = await self.get_by_task_id(db, task_id=task_id)
        if task_result:
            return task_result.get_result_preview(max_length)
        return None

    async def get_recent_results(
        self,
        db: AsyncSession,
        *,
        days: int = 7,
        limit: int = 100
    ) -> List[TaskResult]:
        """최근 N일간 작업 결과 목록 조회"""
        since_date = datetime.now() - timedelta(days=days)
        stmt = select(TaskResult).where(
            TaskResult.created_at >= since_date
        ).order_by(desc(TaskResult.created_at)).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_stats_by_type(self, db: AsyncSession) -> dict:
        """결과 타입별 통계 조회"""
        try:
            stmt = select(
                TaskResult.result_type,
                func.count(TaskResult.id).label('count'),
                func.avg(TaskResult.result_size).label('avg_size'),
                func.sum(TaskResult.result_size).label('total_size')
            ).group_by(TaskResult.result_type)

            result = await db.execute(stmt)
            rows = result.all()

            stats = {}
            for row in rows:
                stats[row.result_type] = {
                    'count': row.count,
                    'avg_size': float(row.avg_size or 0),
                    'total_size': int(row.total_size or 0)
                }
            return stats
        except Exception as e:
            await db.rollback()
            raise e

    async def cleanup_old_results(
        self,
        db: AsyncSession,
        *,
        days: int = 90
    ) -> int:
        """오래된 결과 정리"""
        try:
            
            from sqlalchemy import delete

            cleanup_date = datetime.now() - timedelta(days=days)
            stmt = delete(TaskResult).where(
                TaskResult.created_at < cleanup_date
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            raise e

    async def cleanup_large_results(
        self,
        db: AsyncSession,
        *,
        max_size: int = 100 * 1024 * 1024,  # 100MB
        days: int = 30
    ) -> int:
        """대용량 오래된 결과 정리"""

        from sqlalchemy import delete

        cleanup_date = datetime.now() - timedelta(days=days)
        stmt = delete(TaskResult).where(
            and_(
                TaskResult.result_size >= max_size,
                TaskResult.created_at < cleanup_date
            )
        )
        result = await db.execute(stmt)


    async def get_total_storage_usage(self, db: AsyncSession) -> dict:
        """전체 저장소 사용량 조회"""

        stmt = select(
            func.count(TaskResult.id).label('total_count'),
            func.sum(TaskResult.result_size).label('total_size'),
            func.avg(TaskResult.result_size).label('avg_size'),
            func.max(TaskResult.result_size).label('max_size')
        )

        result = await db.execute(stmt)
        row = result.first()

        return {
            'total_count': row.total_count or 0,
            'total_size': int(row.total_size or 0),
            'avg_size': float(row.avg_size or 0),
            'max_size': int(row.max_size or 0)
        }

    async def get_results_by_task_name(
        self,
        db: AsyncSession,
        *,
        task_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskResult]:
        """작업명별 결과 목록 조회 (작업 로그와 조인)"""

        from ...models.task_log import TaskLog

        stmt = select(TaskResult).join(TaskLog).where(
            TaskLog.task_name == task_name
        ).order_by(desc(TaskResult.created_at)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())



# 인스턴스 생성
task_result = AsyncCRUDTaskResult(TaskResult)