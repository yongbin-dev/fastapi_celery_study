# app/repository/crud/async_crud/ocr_result.py
"""OCR 결과 비동기 CRUD"""

from typing import Optional

from sqlalchemy import select
from supabase import Client

from app.domains.ocr.schemas.ocr_db import OCRTextBoxCreate
from app.models import OCRTextBox
from app.repository.crud.supabase_crud.base import SupabaseCRUDBase


class AsyncCRUDOCRTextBox(
    SupabaseCRUDBase[OCRTextBox, OCRTextBoxCreate, OCRTextBoxCreate]
):
    """OCR 결과 비동기 CRUD 클래스"""

    async def get_all(self, db: Client) -> Optional[list[OCRTextBox]]:
        stmt = select(OCRTextBox)
        result = await db.execute(stmt)
        return list(result.scalars().all())


# 싱글톤 인스턴스
ocr_text_box_crud = AsyncCRUDOCRTextBox(OCRTextBox)
