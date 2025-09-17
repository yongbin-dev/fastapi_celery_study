# crud/async_crud/chain_execution.py

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from datetime import datetime, timedelta

from .base import AsyncCRUDBase
from app.models.chain_execution import ChainExecution
from app.schemas.enums import ProcessStatus


class AsyncCRUDChainExecution(AsyncCRUDBase[ChainExecution, dict, dict]):
    """ChainExecution 모델용 비동기 CRUD 클래스"""

    async def get_all (self , db : AsyncSession )-> Optional[list[ChainExecution]] :
        stmt = select(ChainExecution)
        result = await db.execute(stmt)
        return list(result.scalars().all());

    async def get_by_chain_id(self, db: AsyncSession, *, chain_id: str) -> Optional[ChainExecution]:
        """chain_id로 체인 실행 조회"""
        try:
            stmt = select(ChainExecution).where(ChainExecution.chain_id == chain_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_chain_name(
        self,
        db: AsyncSession,
        *,
        chain_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChainExecution]:
        """chain_name으로 체인 실행 목록 조회"""
        try:
            stmt = select(ChainExecution).where(
                ChainExecution.chain_name == chain_name
            ).order_by(desc(ChainExecution.created_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_status(
        self,
        db: AsyncSession,
        *,
        status: ProcessStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChainExecution]:
        """상태별 체인 실행 목록 조회"""
        try:
            stmt = select(ChainExecution).where(
                ChainExecution.status == status.value
            ).order_by(desc(ChainExecution.created_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_running_chains(self, db: AsyncSession) -> List[ChainExecution]:
        """실행 중인 체인 목록 조회"""
        try:
            stmt = select(ChainExecution).where(
                ChainExecution.status == ProcessStatus.STARTED.value
            ).order_by(desc(ChainExecution.started_at))
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_completed_chains(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChainExecution]:
        """완료된 체인 목록 조회 (성공/실패 포함)"""
        try:
            stmt = select(ChainExecution).where(
                ChainExecution.status.in_([
                    ProcessStatus.SUCCESS.value,
                    ProcessStatus.FAILURE.value,
                    ProcessStatus.REVOKED.value
                ])
            ).order_by(desc(ChainExecution.finished_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_failed_chains(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChainExecution]:
        """실패한 체인 목록 조회"""
        try:
            stmt = select(ChainExecution).where(
                ChainExecution.status == ProcessStatus.FAILURE.value
            ).order_by(desc(ChainExecution.finished_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_initiated_by(
        self,
        db: AsyncSession,
        *,
        initiated_by: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChainExecution]:
        """시작한 사용자/시스템별 체인 실행 목록 조회"""
        try:
            stmt = select(ChainExecution).where(
                ChainExecution.initiated_by == initiated_by
            ).order_by(desc(ChainExecution.created_at)).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def create_chain_execution(
        self,
        db: AsyncSession,
        *,
        chain_id: str,
        chain_name: str,
        total_tasks: int = 4,
        initiated_by: Optional[str] = None,
        input_data: Optional[dict] = None
    ) -> ChainExecution:
        """새 체인 실행 생성"""
        try:
            chain_exec = ChainExecution(
                chain_id=chain_id,
                chain_name=chain_name,
                total_tasks=total_tasks,
                status=ProcessStatus.PENDING.value,
                initiated_by=initiated_by,
                input_data=input_data
            )
            db.add(chain_exec)
            await db.commit()
            await db.refresh(chain_exec)
            return chain_exec
        except Exception as e:
            await db.rollback()
            raise e

    async def start_chain(
        self,
        db: AsyncSession,
        *,
        chain_execution: ChainExecution,
        initiated_by: Optional[str] = None
    ) -> ChainExecution:
        """체인 실행 시작"""
        try:
            chain_execution.start_execution(initiated_by)
            db.add(chain_execution)
            await db.commit()
            await db.refresh(chain_execution)
            return chain_execution
        except Exception as e:
            await db.rollback()
            raise e

    async def complete_chain(
        self,
        db: AsyncSession,
        *,
        chain_execution: ChainExecution,
        success: bool = True,
        final_result: Optional[dict] = None,
        error_message: Optional[str] = None
    ) -> ChainExecution:
        """체인 실행 완료"""
        try:
            chain_execution.complete_execution(success, final_result, error_message)
            db.add(chain_execution)
            await db.commit()
            await db.refresh(chain_execution)
            return chain_execution
        except Exception as e:
            await db.rollback()
            raise e

    async def increment_completed_tasks(
        self,
        db: AsyncSession,
        *,
        chain_execution: ChainExecution
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
        self,
        db: AsyncSession,
        *,
        chain_execution: ChainExecution
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

    async def get_stats_by_status(self, db: AsyncSession) -> dict:
        """상태별 통계 조회"""
        try:
            stats = {}
            for status in ProcessStatus:
                stmt = select(func.count(ChainExecution.id)).where(
                    ChainExecution.status == status.value
                )
                result = await db.execute(stmt)
                count = result.scalar()
                stats[status.value] = count
            return stats
        except Exception as e:
            await db.rollback()
            raise e

    async def get_recent_chains(
        self,
        db: AsyncSession,
        *,
        days: int = 7,
        limit: int = 50
    ) -> List[ChainExecution]:
        """최근 N일간 체인 실행 목록 조회"""
        try:
            

            since_date = datetime.now() - timedelta(days=days)
            stmt = select(ChainExecution).where(
                ChainExecution.created_at >= since_date
            ).order_by(desc(ChainExecution.created_at)).limit(limit)

            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def cleanup_old_chains(
        self,
        db: AsyncSession,
        *,
        days: int = 30
    ) -> int:
        """오래된 완료 체인 정리"""
        try:
            
            from sqlalchemy import delete

            cleanup_date = datetime.now() - timedelta(days=days)
            stmt = delete(ChainExecution).where(
                and_(
                    ChainExecution.finished_at < cleanup_date,
                    ChainExecution.status.in_([
                        ProcessStatus.SUCCESS.value,
                        ProcessStatus.FAILURE.value,
                        ProcessStatus.REVOKED.value
                    ])
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            raise e


# 인스턴스 생성
chain_execution = AsyncCRUDChainExecution(ChainExecution)