# crud/async_crud/batch_execution.py

from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.batch_execution import BatchExecution
from shared.schemas.batch_execution import (
    BatchExecutionCreate,
    BatchExecutionResponse,
    BatchExecutionUpdate,
)
from shared.schemas.enums import ProcessStatus

from .base import AsyncCRUDBase


class AsyncCRUDBatchExecution(
    AsyncCRUDBase[BatchExecution, BatchExecutionCreate, BatchExecutionUpdate]
):
    """BatchExecution 모델용 비동기 CRUD 클래스"""

    async def get_by_batch_id(
        self, db: AsyncSession, *, batch_id: str
    ) -> Optional[BatchExecution]:
        """batch_id로 배치 실행 조회"""
        try:
            stmt = select(BatchExecution).where(
                BatchExecution.batch_id == batch_id
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise e

    async def get_dto_by_batch_id(
        self, db: AsyncSession, *, batch_id: str
    ) -> Optional[BatchExecutionResponse]:
        """batch_id로 배치 실행 조회 (DTO 반환)"""
        try:
            stmt = select(BatchExecution).where(
                BatchExecution.batch_id == batch_id
            )
            result = await db.execute(stmt)
            batch_execution = result.scalar_one_or_none()

            if not batch_execution:
                return None

            # progress_percentage 계산
            response = BatchExecutionResponse.model_validate(batch_execution)
            response.progress_percentage = (
                batch_execution.get_progress_percentage()
            )
            return response
        except Exception as e:
            await db.rollback()
            raise e

    async def create_batch_execution(
        self,
        db: AsyncSession,
        *,
        batch_id: str,
        batch_name: str,
        total_images: int,
        chunk_size: int = 10,
        initiated_by: Optional[str] = None,
        input_data: Optional[dict] = None,
        options: Optional[dict] = None,
    ) -> BatchExecution:
        """새 배치 실행 생성"""
        try:
            # 총 청크 수 계산
            total_chunks = (total_images + chunk_size - 1) // chunk_size

            batch_exec = BatchExecution(
                batch_id=batch_id,
                batch_name=batch_name,
                total_images=total_images,
                total_chunks=total_chunks,
                chunk_size=chunk_size,
                status=ProcessStatus.PENDING.value,
                initiated_by=initiated_by,
                input_data=input_data,
                options=options,
            )
            db.add(batch_exec)
            await db.commit()
            await db.refresh(batch_exec)
            return batch_exec
        except Exception as e:
            await db.rollback()
            raise e

    async def increment_completed_images(
        self, db: AsyncSession, *, batch_execution: BatchExecution, count: int = 1
    ) -> BatchExecution:
        """완료된 이미지 수 증가"""
        try:
            batch_execution.increment_completed_images(count)
            db.add(batch_execution)
            await db.commit()
            await db.refresh(batch_execution)
            return batch_execution
        except Exception as e:
            await db.rollback()
            raise e

    async def increment_failed_images(
        self, db: AsyncSession, *, batch_execution: BatchExecution, count: int = 1
    ) -> BatchExecution:
        """실패한 이미지 수 증가"""
        try:
            batch_execution.increment_failed_images(count)
            db.add(batch_execution)
            await db.commit()
            await db.refresh(batch_execution)
            return batch_execution
        except Exception as e:
            await db.rollback()
            raise e

    async def increment_completed_chunks(
        self, db: AsyncSession, *, batch_execution: BatchExecution
    ) -> BatchExecution:
        """완료된 청크 수 증가"""
        try:
            batch_execution.increment_completed_chunks()
            db.add(batch_execution)
            await db.commit()
            await db.refresh(batch_execution)
            return batch_execution
        except Exception as e:
            await db.rollback()
            raise e

    async def increment_failed_chunks(
        self, db: AsyncSession, *, batch_execution: BatchExecution
    ) -> BatchExecution:
        """실패한 청크 수 증가"""
        try:
            batch_execution.increment_failed_chunks()
            db.add(batch_execution)
            await db.commit()
            await db.refresh(batch_execution)
            return batch_execution
        except Exception as e:
            await db.rollback()
            raise e

    async def update_status(
        self,
        db: AsyncSession,
        *,
        batch_execution: BatchExecution,
        status: ProcessStatus,
    ) -> BatchExecution:
        """배치 실행 상태 업데이트"""
        try:
            batch_execution.status = status
            if status == ProcessStatus.STARTED.value:
                batch_execution.started_at = datetime.now()
            elif status in [
                ProcessStatus.SUCCESS.value,
                ProcessStatus.FAILURE.value,
                ProcessStatus.REVOKED.value,
            ]:
                batch_execution.finished_at = datetime.now()

            db.add(batch_execution)
            await db.commit()
            await db.refresh(batch_execution)
            return batch_execution
        except Exception as e:
            await db.rollback()
            raise e

    async def get_active_batches(
        self, db: AsyncSession
    ) -> List[BatchExecution]:
        """진행 중인 배치 목록 조회"""
        try:
            stmt = select(BatchExecution)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_recent_batches(
        self, db: AsyncSession, *, limit: int = 10
    ) -> List[BatchExecution]:
        """최근 배치 목록 조회"""
        try:
            stmt = (
                select(BatchExecution)
                .order_by(desc(BatchExecution.created_at))
                .limit(limit)
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e


# 인스턴스 생성
async_batch_execution_crud = AsyncCRUDBatchExecution(BatchExecution)
