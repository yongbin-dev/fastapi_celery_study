# app/repository/crud/sync_crud/ocr_text_box.py
"""OCR 텍스트 박스 동기 CRUD (Celery용)"""

from sqlalchemy.orm import Session

from app.domains.ocr.schemas.ocr_db import OCRTextBoxCreate
from app.models import OCRTextBox
from app.repository.crud.sync_crud.base import CRUDBase


class CRUDOCRTextBox(CRUDBase[OCRTextBox, OCRTextBoxCreate, OCRTextBoxCreate]):
    """OCR 텍스트 박스 동기 CRUD 클래스"""

    def create(
        self, session: Session, *, obj_in: OCRTextBoxCreate, ocr_execution_id: int
    ) -> OCRTextBox:
        """텍스트 박스 생성 (ocr_execution_id 포함)"""
        db_obj = OCRTextBox(
            ocr_execution_id=ocr_execution_id,
            text=obj_in.text,
            confidence=obj_in.confidence,
            bbox=obj_in.bbox,
        )
        session.add(db_obj)
        session.flush()
        return db_obj


# 싱글톤 인스턴스
ocr_text_box_crud = CRUDOCRTextBox(OCRTextBox)
