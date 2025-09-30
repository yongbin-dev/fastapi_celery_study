# app/domains/ocr/schemas/__init__.py
"""
OCR 도메인 Pydantic 스키마
"""
from .response import OCRExtractResponse, OCRResultDTO, TextBoxDTO, OCRTextBox
from .request import OCRRequestDTO

__all__ = [
    "OCRExtractResponse",
    "OCRResultDTO",
    "TextBoxDTO",
    "OCRTextBox",
    "OCRRequestDTO",
]