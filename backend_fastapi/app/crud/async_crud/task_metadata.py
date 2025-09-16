# crud/async_crud/task_metadata.py

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_, func
from sqlalchemy.orm import joinedload

from .base import AsyncCRUDBase
from ...models.task_metadata import TaskMetadata


class AsyncCRUDTaskMetadata(AsyncCRUDBase[TaskMetadata, dict, dict]):
    """TaskMetadata 모델용 비동기 CRUD 클래스"""

    async def get_by_task_id(self, db: AsyncSession, *, task_id: str) -> Optional[TaskMetadata]:
        """task_id로 작업 메타데이터 조회"""
        try:
            stmt = select(TaskMetadata).where(TaskMetadata.task_id == task_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_worker(
        self,
        db: AsyncSession,
        *,
        worker_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskMetadata]:
        """워커별 작업 메타데이터 목록 조회"""
        try:
            stmt = select(TaskMetadata).where(
                TaskMetadata.worker_name == worker_name
            ).order_by(desc(TaskMetadata.created_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_queue(
        self,
        db: AsyncSession,
        *,
        queue_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskMetadata]:
        """큐별 작업 메타데이터 목록 조회"""
        try:
            stmt = select(TaskMetadata).where(
                TaskMetadata.queue_name == queue_name
            ).order_by(desc(TaskMetadata.created_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_priority(
        self,
        db: AsyncSession,
        *,
        min_priority: int = 0,
        max_priority: int = 9,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskMetadata]:
        """우선순위별 작업 메타데이터 목록 조회"""
        try:
            stmt = select(TaskMetadata).where(
                and_(
                    TaskMetadata.priority >= min_priority,
                    TaskMetadata.priority <= max_priority
                )
            ).order_by(desc(TaskMetadata.priority), desc(TaskMetadata.created_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_scheduled_tasks(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskMetadata]:
        """예약된 작업들 조회"""
        try:
            from ...models.base import seoul_now

            stmt = select(TaskMetadata).where(
                and_(
                    TaskMetadata.eta.isnot(None),
                    TaskMetadata.eta > seoul_now()
                )
            ).order_by(TaskMetadata.eta).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_expired_tasks(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskMetadata]:
        """만료된 작업들 조회"""
        try:
            from ...models.base import seoul_now

            stmt = select(TaskMetadata).where(
                and_(
                    TaskMetadata.expires.isnot(None),
                    TaskMetadata.expires < seoul_now()
                )
            ).order_by(desc(TaskMetadata.expires)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_parent_id(
        self,
        db: AsyncSession,
        *,
        parent_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskMetadata]:
        """부모 작업 ID로 자식 작업들 조회"""
        try:
            stmt = select(TaskMetadata).where(
                TaskMetadata.parent_id == parent_id
            ).order_by(desc(TaskMetadata.created_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_root_id(
        self,
        db: AsyncSession,
        *,
        root_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskMetadata]:
        """루트 작업 ID로 워크플로우 작업들 조회"""
        try:
            stmt = select(TaskMetadata).where(
                TaskMetadata.root_id == root_id
            ).order_by(desc(TaskMetadata.created_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_with_task(
        self,
        db: AsyncSession,
        *,
        task_id: str
    ) -> Optional[TaskMetadata]:
        """작업 로그와 함께 메타데이터 조회"""
        try:
            stmt = select(TaskMetadata).options(
                joinedload(TaskMetadata.task)
            ).where(TaskMetadata.task_id == task_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise e

    async def create_task_metadata(
        self,
        db: AsyncSession,
        *,
        task_id: str,
        worker_name: Optional[str] = None,
        queue_name: str = "default",
        priority: int = 0,
        eta: Optional[datetime] = None,
        expires: Optional[datetime] = None,
        parent_id: Optional[str] = None,
        root_id: Optional[str] = None,
        **kwargs
    ) -> TaskMetadata:
        """새 작업 메타데이터 생성"""
        try:
            metadata = TaskMetadata(
                task_id=task_id,
                worker_name=worker_name,
                queue_name=queue_name,
                priority=priority,
                eta=eta,
                expires=expires,
                parent_id=parent_id,
                root_id=root_id,
                **kwargs
            )
            db.add(metadata)
            await db.commit()
            await db.refresh(metadata)
            return metadata
        except Exception as e:
            await db.rollback()
            raise e

    async def update_worker_info(
        self,
        db: AsyncSession,
        *,
        metadata: TaskMetadata,
        worker_name: str,
        queue_name: Optional[str] = None
    ) -> TaskMetadata:
        """워커 정보 업데이트"""
        try:
            metadata.worker_name = worker_name
            if queue_name:
                metadata.queue_name = queue_name

            db.add(metadata)
            await db.commit()
            await db.refresh(metadata)
            return metadata
        except Exception as e:
            await db.rollback()
            raise e

    async def get_worker_statistics(self, db: AsyncSession) -> List[dict]:
        """워커별 통계 조회"""
        try:
            stmt = select(
                TaskMetadata.worker_name,
                func.count(TaskMetadata.id).label('task_count'),
                func.avg(TaskMetadata.priority).label('avg_priority'),
                func.count(TaskMetadata.queue_name).label('queue_diversity')
            ).where(
                TaskMetadata.worker_name.isnot(None)
            ).group_by(TaskMetadata.worker_name).order_by(desc('task_count'))

            result = await db.execute(stmt)
            rows = result.all()

            return [
                {
                    'worker_name': row.worker_name,
                    'task_count': row.task_count,
                    'avg_priority': float(row.avg_priority or 0),
                    'queue_diversity': row.queue_diversity
                }
                for row in rows
            ]
        except Exception as e:
            await db.rollback()
            raise e

    async def get_queue_statistics(self, db: AsyncSession) -> List[dict]:
        """큐별 통계 조회"""
        try:
            stmt = select(
                TaskMetadata.queue_name,
                func.count(TaskMetadata.id).label('task_count'),
                func.avg(TaskMetadata.priority).label('avg_priority'),
                func.count(func.distinct(TaskMetadata.worker_name)).label('worker_count')
            ).group_by(TaskMetadata.queue_name).order_by(desc('task_count'))

            result = await db.execute(stmt)
            rows = result.all()

            return [
                {
                    'queue_name': row.queue_name,
                    'task_count': row.task_count,
                    'avg_priority': float(row.avg_priority or 0),
                    'worker_count': row.worker_count
                }
                for row in rows
            ]
        except Exception as e:
            await db.rollback()
            raise e

    async def get_priority_distribution(self, db: AsyncSession) -> dict:
        """우선순위 분포 조회"""
        try:
            stmt = select(
                TaskMetadata.priority,
                func.count(TaskMetadata.id).label('count')
            ).group_by(TaskMetadata.priority).order_by(TaskMetadata.priority)

            result = await db.execute(stmt)
            rows = result.all()

            distribution = {}
            for row in rows:
                distribution[row.priority] = row.count

            return distribution
        except Exception as e:
            await db.rollback()
            raise e

    async def get_scheduled_count(self, db: AsyncSession) -> int:
        """예약된 작업 수 조회"""
        try:
            from ...models.base import seoul_now

            stmt = select(func.count(TaskMetadata.id)).where(
                and_(
                    TaskMetadata.eta.isnot(None),
                    TaskMetadata.eta > seoul_now()
                )
            )
            result = await db.execute(stmt)
            return result.scalar()
        except Exception as e:
            await db.rollback()
            raise e

    async def get_expired_count(self, db: AsyncSession) -> int:
        """만료된 작업 수 조회"""
        try:
            from ...models.base import seoul_now

            stmt = select(func.count(TaskMetadata.id)).where(
                and_(
                    TaskMetadata.expires.isnot(None),
                    TaskMetadata.expires < seoul_now()
                )
            )
            result = await db.execute(stmt)
            return result.scalar()
        except Exception as e:
            await db.rollback()
            raise e

    async def get_workflow_tree(
        self,
        db: AsyncSession,
        *,
        root_id: str
    ) -> dict:
        """워크플로우 트리 구조 조회"""
        try:
            # 루트 작업 조회
            root_stmt = select(TaskMetadata).where(
                and_(
                    TaskMetadata.root_id == root_id,
                    TaskMetadata.parent_id.is_(None)
                )
            )
            root_result = await db.execute(root_stmt)
            root_metadata = root_result.scalar_one_or_none()

            if not root_metadata:
                return {}

            # 모든 워크플로우 작업들 조회
            all_stmt = select(TaskMetadata).where(TaskMetadata.root_id == root_id)
            all_result = await db.execute(all_stmt)
            all_tasks = list(all_result.scalars().all())

            # 트리 구조 생성
            task_dict = {task.task_id: task for task in all_tasks}
            tree = {'root': root_metadata.to_dict(), 'children': {}}

            def build_children(parent_id: str) -> dict:
                children = {}
                for task in all_tasks:
                    if task.parent_id == parent_id:
                        children[task.task_id] = {
                            'task': task.to_dict(),
                            'children': build_children(task.task_id)
                        }
                return children

            tree['children'] = build_children(root_metadata.task_id)
            return tree
        except Exception as e:
            await db.rollback()
            raise e

    async def cleanup_expired_metadata(self, db: AsyncSession) -> int:
        """만료된 메타데이터 정리"""
        try:
            from ...models.base import seoul_now
            from sqlalchemy import delete

            stmt = delete(TaskMetadata).where(
                and_(
                    TaskMetadata.expires.isnot(None),
                    TaskMetadata.expires < seoul_now()
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            raise e

    async def get_recent_tasks_by_worker(
        self,
        db: AsyncSession,
        *,
        worker_name: str,
        days: int = 7,
        limit: int = 100
    ) -> List[TaskMetadata]:
        """최근 N일간 특정 워커의 작업들 조회"""
        try:
            from ...models.base import seoul_now

            since_date = seoul_now() - timedelta(days=days)
            stmt = select(TaskMetadata).where(
                and_(
                    TaskMetadata.worker_name == worker_name,
                    TaskMetadata.created_at >= since_date
                )
            ).order_by(desc(TaskMetadata.created_at)).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e


# 인스턴스 생성
task_metadata = AsyncCRUDTaskMetadata(TaskMetadata)