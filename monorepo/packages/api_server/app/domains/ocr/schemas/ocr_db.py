# app/domains/ocr/schemas/ocr_db.py
"""OCR DB 스키마 - shared 패키지에서 재사용"""

from shared.schemas.ocr_db import OCRExecutionCreate, OCRTextBoxCreate

__all__ = [
    "OCRExecutionCreate",
    "OCRTextBoxCreate",
]
