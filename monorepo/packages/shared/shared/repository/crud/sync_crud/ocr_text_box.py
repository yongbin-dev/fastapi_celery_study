# app/repository/crud/sync_crud/ocr_text_box.py
"""OCR 텍스트 박스 동기 CRUD (Celery용)"""


from shared.models import OCRTextBox
from shared.repository.crud.sync_crud.base import CRUDBase
from shared.schemas.ocr_db import OCRTextBoxCreate


class CRUDOCRTextBox(CRUDBase[OCRTextBox, OCRTextBoxCreate, OCRTextBoxCreate]):
    """OCR 텍스트 박스 동기 CRUD 클래스"""
    pass

# 싱글톤 인스턴스
ocr_text_box_crud = CRUDOCRTextBox(OCRTextBox)
