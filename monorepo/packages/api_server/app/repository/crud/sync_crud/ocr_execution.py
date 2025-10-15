# app/repository/crud/sync_crud/ocr_execution.py
"""OCR 실행 정보 동기 CRUD (Celery용)"""

from typing import Optional

from domains.ocr.schemas.ocr_db import OCRExecutionCreate
from repository.crud.sync_crud.base import CRUDBase
from sqlalchemy.orm import Session

from shared.models import OCRExecution


class CRUDOCRExecution(CRUDBase[OCRExecution, OCRExecutionCreate, OCRExecutionCreate]):
    """OCR 실행 정보 동기 CRUD 클래스"""

    def get_by_chain_id(self, session: Session, *, id: str) -> Optional[OCRExecution]:
        """chain_id로 OCR 실행 조회"""
        return session.query(OCRExecution).filter(OCRExecution.id == id).first()


# 싱글톤 인스턴스
ocr_execution_crud = CRUDOCRExecution(OCRExecution)
