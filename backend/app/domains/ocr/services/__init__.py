# app/domains/ocr/services/__init__.py
"""
OCR 서비스 레이어
"""
from .ocr_model import OCRModel, get_ocr_model
from .ocr_service import OCRService, get_ocr_service

__all__ = ["OCRModel", "OCRService", "get_ocr_service", "get_ocr_model"]
