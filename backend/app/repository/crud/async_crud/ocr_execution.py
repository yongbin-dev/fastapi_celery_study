# app/repository/crud/async_crud/ocr_execution.py
"""OCR 실행 정보 비동기 CRUD"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ocr.schemas.ocr_db import OCRExecutionCreate
from app.models import OCRExecution
from app.repository.crud.async_crud.base import AsyncCRUDBase


class AsyncCRUDOCRExecution(
    AsyncCRUDBase[OCRExecution, OCRExecutionCreate, OCRExecutionCreate]
):
    """OCR 실행 정보 비동기 CRUD 클래스"""

    async def get_all(self, db: AsyncSession) -> list[OCRExecution]:
        stmt = select(OCRExecution)
        result = await db.execute(stmt)
        return list(result.scalars().all())


# 싱글톤 인스턴스
ocr_execution_crud = AsyncCRUDOCRExecution(OCRExecution)
