# app/domains/ocr/services/__init__.py
"""
OCR 서비스 레이어
"""
from .ocr_model import OCRModel
from .ocr_service import OCRService

__all__ = ["OCRModel", "OCRService"]