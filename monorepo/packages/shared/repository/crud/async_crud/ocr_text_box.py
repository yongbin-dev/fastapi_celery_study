# app/repository/crud/async_crud/ocr_result.py
"""OCR 결과 비동기 CRUD"""

from typing import Optional

from ...schemas.ocr_db import OCRTextBoxCreate
from ...repository.crud.async_crud.base import AsyncCRUDBase
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import OCRTextBox


class AsyncCRUDOCRTextBox(
    AsyncCRUDBase[OCRTextBox, OCRTextBoxCreate, OCRTextBoxCreate]
):
    """OCR 결과 비동기 CRUD 클래스"""

    async def get_all(self, db: AsyncSession) -> Optional[list[OCRTextBox]]:
        stmt = select(OCRTextBox)
        result = await db.execute(stmt)
        return list(result.scalars().all())


# 싱글톤 인스턴스
ocr_text_box_crud = AsyncCRUDOCRTextBox(OCRTextBox)
