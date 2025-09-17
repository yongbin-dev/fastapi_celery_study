# crud/async_crud/task_log.py

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from datetime import timedelta

from .base import AsyncCRUDBase
from ...models.task_log import TaskLog


class AsyncCRUDTaskLog(AsyncCRUDBase[TaskLog, dict, dict]):
    """TaskLog 모델용 비동기 CRUD 클래스"""

    async def get_by_task_id(self, db: AsyncSession, *, task_id: str) -> Optional[TaskLog]:
        """task_id로 작업 로그 조회"""
        try:
            stmt = select(TaskLog).where(TaskLog.task_id == task_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_task_name(
        self,
        db: AsyncSession,
        *,
        task_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskLog]:
        """task_name으로 작업 로그 목록 조회"""
        try:
            stmt = select(TaskLog).where(
                TaskLog.task_name == task_name
            ).order_by(desc(TaskLog.created_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_status(
        self,
        db: AsyncSession,
        *,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskLog]:
        """상태별 작업 로그 목록 조회"""
        try:
            stmt = select(TaskLog).where(
                TaskLog.status == status
            ).order_by(desc(TaskLog.created_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_running_tasks(self, db: AsyncSession) -> List[TaskLog]:
        """실행 중인 작업 목록 조회"""
        try:
            stmt = select(TaskLog).where(
                TaskLog.status == 'STARTED'
            ).order_by(desc(TaskLog.started_at))
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_failed_tasks(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskLog]:
        """실패한 작업 목록 조회"""
        try:
            stmt = select(TaskLog).where(
                TaskLog.status == 'FAILURE'
            ).order_by(desc(TaskLog.created_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_completed_tasks(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[TaskLog]:
        """완료된 작업 목록 조회"""
        try:
            stmt = select(TaskLog).where(
                TaskLog.status.in_(['SUCCESS', 'FAILURE', 'REVOKED'])
            ).order_by(desc(TaskLog.completed_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def create_task_log(
        self,
        db: AsyncSession,
        *,
        task_id: str,
        task_name: str,
        status: str = 'PENDING',
        args: Optional[str] = None,
        kwargs: Optional[str] = None
    ) -> TaskLog:
        """새 작업 로그 생성"""
        try:
            task_log = TaskLog(
                task_id=task_id,
                task_name=task_name,
                status=status,
                args=args,
                kwargs=kwargs
            )
            db.add(task_log)
            await db.commit()
            await db.refresh(task_log)
            return task_log
        except Exception as e:
            await db.rollback()
            raise e

    async def update_status(
        self,
        db: AsyncSession,
        *,
        task_log: TaskLog,
        status: str,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> TaskLog:
        """작업 상태 업데이트"""
        try:
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
            await db.commit()
            await db.refresh(task_log)
            return task_log
        except Exception as e:
            await db.rollback()
            raise e

    async def increment_retries(
        self,
        db: AsyncSession,
        *,
        task_log: TaskLog
    ) -> TaskLog:
        """재시도 횟수 증가"""
        try:
            task_log.retries += 1
            db.add(task_log)
            await db.commit()
            await db.refresh(task_log)
            return task_log
        except Exception as e:
            await db.rollback()
            raise e

    async def get_pipeline_tasks_by_chain(
        self,
        db: AsyncSession,
        *,
        chain_id: str
    ) -> List[TaskLog]:
        """특정 체인의 파이프라인 작업들을 단계순으로 조회"""
        try:
            stage_tasks = []
            for stage_num in range(1, 5):  # stage1~4
                # 각 stage별 TaskLog 조회 - chain_id로 필터링
                stmt = select(TaskLog).where(
                    and_(
                        TaskLog.task_name.like(f"app.tasks.stage{stage_num}_%"),
                        # kwargs에서 chain_id 매칭 또는 args에서 chain_id 매칭
                        TaskLog.kwargs.like(f'%"{chain_id}"%')
                    )
                ).order_by(desc(TaskLog.created_at)).limit(1)

                result = await db.execute(stmt)
                task = result.scalar_one_or_none()

                if task:
                    stage_tasks.append(task)
                else:
                    # 더 넓은 검색 - args에서도 찾아보기
                    stmt_alt = select(TaskLog).where(
                        and_(
                            TaskLog.task_name.like(f"app.tasks.stage{stage_num}_%"),
                            TaskLog.args.like(f'%{chain_id}%')
                        )
                    ).order_by(desc(TaskLog.created_at)).limit(1)

                    result_alt = await db.execute(stmt_alt)
                    task_alt = result_alt.scalar_one_or_none()
                    if task_alt:
                        stage_tasks.append(task_alt)

            return stage_tasks
        except Exception as e:
            await db.rollback()
            raise e

    async def get_recent_tasks(
        self,
        db: AsyncSession,
        *,
        days: int = 7,
        limit: int = 100
    ) -> List[TaskLog]:
        """최근 N일간 작업 로그 목록 조회"""
        try:
            

            since_date = datetime.now() - timedelta(days=days)
            stmt = select(TaskLog).where(
                TaskLog.created_at >= since_date
            ).order_by(desc(TaskLog.created_at)).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_stats_by_status(self, db: AsyncSession) -> dict:
        """상태별 통계 조회"""
        try:
            statuses = ['PENDING', 'STARTED', 'SUCCESS', 'FAILURE', 'RETRY', 'REVOKED']
            stats = {}
            for status in statuses:
                stmt = select(func.count(TaskLog.id)).where(TaskLog.status == status)
                result = await db.execute(stmt)
                count = result.scalar()
                stats[status] = count
            return stats
        except Exception as e:
            await db.rollback()
            raise e

    async def get_task_performance_stats(self, db: AsyncSession, *, task_name: str) -> dict:
        """특정 작업의 성능 통계"""
        try:
            # 성공한 작업들의 실행 시간 통계
            stmt = select(
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
            ).where(
                and_(
                    TaskLog.task_name == task_name,
                    TaskLog.status == 'SUCCESS',
                    TaskLog.started_at.isnot(None),
                    TaskLog.completed_at.isnot(None)
                )
            )

            result = await db.execute(stmt)
            row = result.first()

            return {
                'total_count': row.total_count or 0,
                'avg_duration': float(row.avg_duration or 0),
                'min_duration': float(row.min_duration or 0),
                'max_duration': float(row.max_duration or 0)
            }
        except Exception as e:
            await db.rollback()
            raise e

    async def cleanup_old_logs(
        self,
        db: AsyncSession,
        *,
        days: int = 90
    ) -> int:
        """오래된 완료 로그 정리"""
        try:
            
            from sqlalchemy import delete

            cleanup_date = datetime.now() - timedelta(days=days)
            stmt = delete(TaskLog).where(
                and_(
                    TaskLog.completed_at < cleanup_date,
                    TaskLog.status.in_(['SUCCESS', 'FAILURE', 'REVOKED'])
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            raise e


# 인스턴스 생성
task_log = AsyncCRUDTaskLog(TaskLog)