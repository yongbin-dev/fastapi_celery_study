# crud/async_crud/task_execution_history.py

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from sqlalchemy.orm import joinedload
from datetime import timedelta

from .base import AsyncCRUDBase
from app.models.task_execution_history import TaskExecutionHistory


class AsyncCRUDTaskExecutionHistory(AsyncCRUDBase[TaskExecutionHistory, dict, dict]):
    """TaskExecutionHistory 모델용 비동기 CRUD 클래스"""

    async def get_by_task_id(
        self, db: AsyncSession, *, task_id: str, skip: int = 0, limit: int = 100
    ) -> List[TaskExecutionHistory]:
        """task_id로 실행 이력 목록 조회"""
        try:
            stmt = (
                select(TaskExecutionHistory)
                .where(TaskExecutionHistory.task_id == task_id)
                .order_by(desc(TaskExecutionHistory.attempt_number))
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_task_id_and_attempt(
        self, db: AsyncSession, *, task_id: str, attempt_number: int
    ) -> Optional[TaskExecutionHistory]:
        """task_id와 시도 번호로 특정 실행 이력 조회"""
        try:
            stmt = select(TaskExecutionHistory).where(
                and_(
                    TaskExecutionHistory.task_id == task_id,
                    TaskExecutionHistory.attempt_number == attempt_number,
                )
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise e

    async def get_latest_attempt(
        self, db: AsyncSession, *, task_id: str
    ) -> Optional[TaskExecutionHistory]:
        """특정 작업의 최신 시도 조회"""
        try:
            stmt = (
                select(TaskExecutionHistory)
                .where(TaskExecutionHistory.task_id == task_id)
                .order_by(desc(TaskExecutionHistory.attempt_number))
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_status(
        self, db: AsyncSession, *, status: str, skip: int = 0, limit: int = 100
    ) -> List[TaskExecutionHistory]:
        """상태별 실행 이력 목록 조회"""
        try:
            stmt = (
                select(TaskExecutionHistory)
                .where(TaskExecutionHistory.status == status)
                .order_by(desc(TaskExecutionHistory.created_at))
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_failed_attempts(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[TaskExecutionHistory]:
        """실패한 시도들 조회"""
        try:
            stmt = (
                select(TaskExecutionHistory)
                .where(TaskExecutionHistory.status.in_(["FAILURE", "TIMEOUT"]))
                .order_by(desc(TaskExecutionHistory.created_at))
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_with_task(
        self, db: AsyncSession, *, task_id: str
    ) -> List[TaskExecutionHistory]:
        """작업 로그와 함께 실행 이력 조회"""
        try:
            stmt = (
                select(TaskExecutionHistory)
                .options(joinedload(TaskExecutionHistory.task))
                .where(TaskExecutionHistory.task_id == task_id)
                .order_by(desc(TaskExecutionHistory.attempt_number))
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def create_attempt(
        self,
        db: AsyncSession,
        *,
        task_id: str,
        attempt_number: int,
        status: str = "STARTED",
    ) -> TaskExecutionHistory:
        """새 시도 기록 생성"""
        try:
            execution_history = TaskExecutionHistory(
                task_id=task_id,
                attempt_number=attempt_number,
                status=status,
                started_at=datetime.now(),
            )
            db.add(execution_history)
            await db.commit()
            await db.refresh(execution_history)
            return execution_history
        except Exception as e:
            await db.rollback()
            raise e

    async def complete_attempt(
        self,
        db: AsyncSession,
        *,
        execution_history: TaskExecutionHistory,
        status: str,
        error_message: Optional[str] = None,
        traceback: Optional[str] = None,
    ) -> TaskExecutionHistory:
        """시도 완료 처리"""
        try:
            execution_history.status = status
            execution_history.completed_at = datetime.now()

            if error_message:
                execution_history.error_message = error_message
            if traceback:
                execution_history.traceback = traceback

            db.add(execution_history)
            await db.commit()
            await db.refresh(execution_history)
            return execution_history
        except Exception as e:
            await db.rollback()
            raise e

    async def get_retry_count(self, db: AsyncSession, *, task_id: str) -> int:
        """특정 작업의 재시도 횟수 조회"""
        try:
            stmt = select(func.count(TaskExecutionHistory.id)).where(
                TaskExecutionHistory.task_id == task_id
            )
            result = await db.execute(stmt)
            return result.scalar()
        except Exception as e:
            await db.rollback()
            raise e

    async def get_failure_patterns(
        self, db: AsyncSession, *, limit: int = 100
    ) -> List[dict]:
        """실패 패턴 분석"""
        try:
            stmt = (
                select(
                    func.substring(TaskExecutionHistory.error_message, 1, 100).label(
                        "error_pattern"
                    ),
                    func.count(TaskExecutionHistory.id).label("count"),
                )
                .where(TaskExecutionHistory.status.in_(["FAILURE", "TIMEOUT"]))
                .group_by(func.substring(TaskExecutionHistory.error_message, 1, 100))
                .order_by(desc("count"))
                .limit(limit)
            )

            result = await db.execute(stmt)
            rows = result.all()

            return [
                {"error_pattern": row.error_pattern, "count": row.count} for row in rows
            ]
        except Exception as e:
            await db.rollback()
            raise e

    async def get_execution_stats(
        self, db: AsyncSession, *, task_id: Optional[str] = None
    ) -> dict:
        """실행 통계 조회"""
        try:
            stmt = select(
                func.count(TaskExecutionHistory.id).label("total_attempts"),
                func.sum(
                    func.case((TaskExecutionHistory.status == "SUCCESS", 1), else_=0)
                ).label("success_count"),
                func.sum(
                    func.case(
                        (TaskExecutionHistory.status.in_(["FAILURE", "TIMEOUT"]), 1),
                        else_=0,
                    )
                ).label("failure_count"),
                func.avg(
                    func.case(
                        (
                            and_(
                                TaskExecutionHistory.started_at.isnot(None),
                                TaskExecutionHistory.completed_at.isnot(None),
                            ),
                            func.extract(
                                "epoch",
                                TaskExecutionHistory.completed_at
                                - TaskExecutionHistory.started_at,
                            ),
                        ),
                        else_=None,
                    )
                ).label("avg_duration"),
            )

            if task_id:
                stmt = stmt.where(TaskExecutionHistory.task_id == task_id)

            result = await db.execute(stmt)
            row = result.first()

            total_attempts = row.total_attempts or 0
            success_count = row.success_count or 0
            failure_count = row.failure_count or 0

            return {
                "total_attempts": total_attempts,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": round(
                    (success_count / total_attempts * 100) if total_attempts > 0 else 0,
                    2,
                ),
                "failure_rate": round(
                    (failure_count / total_attempts * 100) if total_attempts > 0 else 0,
                    2,
                ),
                "avg_duration": float(row.avg_duration or 0),
            }
        except Exception as e:
            await db.rollback()
            raise e

    async def get_recent_failures(
        self, db: AsyncSession, *, days: int = 7, limit: int = 50
    ) -> List[TaskExecutionHistory]:
        """최근 N일간 실패한 시도들 조회"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            stmt = (
                select(TaskExecutionHistory)
                .where(
                    and_(
                        TaskExecutionHistory.status.in_(["FAILURE", "TIMEOUT"]),
                        TaskExecutionHistory.created_at >= since_date,
                    )
                )
                .order_by(desc(TaskExecutionHistory.created_at))
                .limit(limit)
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def get_long_running_attempts(
        self,
        db: AsyncSession,
        *,
        min_duration_seconds: int = 300,  # 5분
        limit: int = 50,
    ) -> List[TaskExecutionHistory]:
        """장시간 실행된 시도들 조회"""
        try:
            stmt = (
                select(TaskExecutionHistory)
                .where(
                    and_(
                        TaskExecutionHistory.started_at.isnot(None),
                        TaskExecutionHistory.completed_at.isnot(None),
                        func.extract(
                            "epoch",
                            TaskExecutionHistory.completed_at
                            - TaskExecutionHistory.started_at,
                        )
                        >= min_duration_seconds,
                    )
                )
                .order_by(
                    desc(
                        func.extract(
                            "epoch",
                            TaskExecutionHistory.completed_at
                            - TaskExecutionHistory.started_at,
                        )
                    )
                )
                .limit(limit)
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await db.rollback()
            raise e

    async def cleanup_old_history(self, db: AsyncSession, *, days: int = 180) -> int:
        """오래된 실행 이력 정리"""
        try:
            from sqlalchemy import delete

            cleanup_date = datetime.now() - timedelta(days=days)
            stmt = delete(TaskExecutionHistory).where(
                TaskExecutionHistory.created_at < cleanup_date
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            raise e

    async def get_task_reliability_score(
        self, db: AsyncSession, *, task_id: str
    ) -> dict:
        """작업 신뢰성 점수 계산"""
        stats = await self.get_execution_stats(db, task_id=task_id)

        if stats["total_attempts"] == 0:
            return {"reliability_score": 0, "grade": "N/A", "total_attempts": 0}

        success_rate = stats["success_rate"]

        # 신뢰성 등급 계산
        if success_rate >= 95:
            grade = "A"
        elif success_rate >= 85:
            grade = "B"
        elif success_rate >= 70:
            grade = "C"
        elif success_rate >= 50:
            grade = "D"
        else:
            grade = "F"

        return {
            "reliability_score": success_rate,
            "grade": grade,
            "total_attempts": stats["total_attempts"],
            "success_count": stats["success_count"],
            "failure_count": stats["failure_count"],
        }


# 인스턴스 생성
task_execution_history = AsyncCRUDTaskExecutionHistory(TaskExecutionHistory)
