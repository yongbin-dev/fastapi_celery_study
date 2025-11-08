# crud/async_crud/chain_execution.py

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.models.chain_execution import ChainExecution
from shared.schemas.chain_execution import (
    ChainExecutionCreate,
    ChainExecutionUpdate,
)
from shared.schemas.enums import ProcessStatus

from .base import AsyncCRUDBase


class AsyncCRUDChainExecution(
    AsyncCRUDBase[ChainExecution, ChainExecutionCreate, ChainExecutionUpdate]
):
    """ChainExecution 모델용 비동기 CRUD 클래스"""

    async def get_all(self, db: AsyncSession) -> Optional[list[ChainExecution]]:
        stmt = select(ChainExecution)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_chain_id(
        self, db: AsyncSession, *, chain_id: str
    ) -> Optional[ChainExecution]:
        """chain_id로 체인 실행 조회"""
        try:
            stmt = select(ChainExecution).where(ChainExecution.chain_id == chain_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise e

    async def create_chain_execution(
        self,
        db: AsyncSession,
        *,
        chain_id: str,
        chain_name: str,
        batch_id: Optional[str] = None,
        total_tasks: int = 4,
        initiated_by: Optional[str] = None,
        input_data: Optional[dict] = None,
    ) -> ChainExecution:
        """새 체인 실행 생성"""
        try:
            # batch_id가 빈 문자열이면 None으로 변환 (외래 키 제약 조건 위반 방지)
            batch_id = batch_id if batch_id else None

            chain_exec = ChainExecution(
                chain_id=chain_id,
                chain_name=chain_name,
                batch_id=batch_id,
                total_tasks=total_tasks,
                status=ProcessStatus.PENDING.value,
                initiated_by=initiated_by,
                input_data=input_data,
            )
            db.add(chain_exec)
            await db.commit()
            await db.refresh(chain_exec)
            return chain_exec
        except Exception as e:
            await db.rollback()
            raise e

    async def increment_completed_tasks(
        self, db: AsyncSession, *, chain_execution: ChainExecution
    ) -> ChainExecution:
        """완료된 작업 수 증가"""
        try:
            chain_execution.increment_completed_tasks()
            db.add(chain_execution)
            await db.commit()
            await db.refresh(chain_execution)
            return chain_execution
        except Exception as e:
            await db.rollback()
            raise e

    async def increment_failed_tasks(
        self, db: AsyncSession, *, chain_execution: ChainExecution
    ) -> ChainExecution:
        """실패한 작업 수 증가"""
        try:
            chain_execution.increment_failed_tasks()
            db.add(chain_execution)
            await db.commit()
            await db.refresh(chain_execution)
            return chain_execution
        except Exception as e:
            await db.rollback()
            raise e

    async def get_with_task_logs(
        self, db: AsyncSession, *, chain_id: str
    ) -> Optional[ChainExecution]:
        """TaskLog와 함께 체인 실행 조회 (Spring의 fetch join과 유사)"""
        stmt = (
            select(ChainExecution)
            .options(selectinload(ChainExecution.task_logs))
            .where(ChainExecution.chain_id == chain_id)
            .order_by(desc(ChainExecution.created_at))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_with_task_logs(
        self,
        db: AsyncSession,
        *,
        days: int = 7,
        limit: int = 100,
    ) -> list[ChainExecution]:
        """TaskLog와 함께 여러 체인 실행 조회"""
        cutoff_date = datetime.now() - timedelta(days=days)

        stmt = (
            select(ChainExecution)
            .options(selectinload(ChainExecution.task_logs))
            .where(ChainExecution.created_at > cutoff_date)
            .order_by(desc(ChainExecution.created_at))
            .limit(limit)
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        db: AsyncSession,
        *,
        chain_execution: ChainExecution,
        status: ProcessStatus,
    ) -> ChainExecution:
        """체인 실행 상태 업데이트"""
        chain_execution.status = status
        if status == ProcessStatus.STARTED.value:
            chain_execution.started_at = datetime.now()
        elif status in [
            ProcessStatus.SUCCESS.value,
            ProcessStatus.FAILURE.value,
            ProcessStatus.REVOKED.value,
        ]:
            chain_execution.finished_at = datetime.now()

        db.add(chain_execution)
        await db.commit()
        await db.refresh(chain_execution)
        return chain_execution


# 인스턴스 생성
chain_execution_crud = AsyncCRUDChainExecution(ChainExecution)

# async def get_by_initiated_by(
#     self, db: AsyncSession, *, initiated_by: str, skip: int = 0, limit: int = 100
# ) -> List[ChainExecution]:
#     """시작한 사용자/시스템별 체인 실행 목록 조회"""
#     try:
#         stmt = (
#             select(ChainExecution)
#             .where(ChainExecution.initiated_by == initiated_by)
#             .order_by(desc(ChainExecution.created_at))
#             .offset(skip)
#             .limit(limit)
#         )
#         result = await db.execute(stmt)
#         return list(result.scalars().all())
#     except Exception as e:
#         await db.rollback()
#         raise e

# async def get_with_task_logs_joinedload(
#     self, db: AsyncSession, *, chain_id: str
# ) -> Optional[ChainExecution]:
#     """joinedload를 사용한 TaskLog와 함께 체인 실행 조회 (한 번의 쿼리로 JOIN)"""
#     try:
#         stmt = (
#             select(ChainExecution)
#             .options(joinedload(ChainExecution.task_logs))
#             .where(ChainExecution.chain_id == chain_id)
#         )
#         result = await db.execute(stmt)
#         return result.unique().scalar_one_or_none()
#     except Exception as e:
#         await db.rollback()
#         raise e
