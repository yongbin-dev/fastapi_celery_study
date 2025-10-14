# app/domains/ocr/services/__init__.py
"""
OCR 서비스 레이어
"""

from .ocr_service import OCRService, get_ocr_service

__all__ = [ "OCRService", "get_ocr_service"]
