# app/domains/ocr/schemas/__init__.py
"""
OCR 도메인 Pydantic 스키마
"""

from .request import OCRRequestDTO
from .response import OCRExtractResponse, OCRResultDTO, OCRTextBox, TextBoxDTO

__all__ = [
    "OCRExtractResponse",
    "OCRResultDTO",
    "TextBoxDTO",
    "OCRTextBox",
    "OCRRequestDTO",
]
