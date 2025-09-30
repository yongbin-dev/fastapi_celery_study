# app/domains/ocr/schemas/__init__.py
"""
OCR 도메인 Pydantic 스키마
"""
from .request import OCRExtractRequest
from .response import OCRExtractResponse

__all__ = ["OCRExtractRequest", "OCRExtractResponse"]