# app/repository/crud/async_crud/ocr_execution.py
"""OCR 실행 정보 비동기 CRUD"""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.models import OCRExecution
from shared.repository.crud.async_crud.base import AsyncCRUDBase
from shared.schemas.ocr_db import OCRExecutionCreate


class AsyncCRUDOCRExecution(
    AsyncCRUDBase[OCRExecution, OCRExecutionCreate, OCRExecutionCreate]
):
    """OCR 실행 정보 비동기 CRUD 클래스"""

    async def get_all(self, db: AsyncSession) -> list[OCRExecution]:
        stmt = select(OCRExecution)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_multi_with_text_box(
        self,
        db: AsyncSession,
        *,
        days: int = 7,
        limit: int = 100,
    ) -> list[OCRExecution]:
        """TaskLog와 함께 여러 체인 실행 조회"""

        stmt = (
            select(OCRExecution)
            .options(selectinload(OCRExecution.text_boxes))
            .order_by(desc(OCRExecution.created_at))
            .limit(limit)
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())


# 싱글톤 인스턴스
ocr_execution_crud = AsyncCRUDOCRExecution(OCRExecution)
