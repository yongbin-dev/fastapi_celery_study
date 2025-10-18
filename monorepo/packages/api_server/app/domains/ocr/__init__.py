# app/domains/ocr/__init__.py
"""
OCR 도메인 모듈
"""

from .controllers.ocr_controller import router as ocr_controller
from .schemas import OCRRequestDTO, OCRResultDTO

__all__ = ["OCRResultDTO", "OCRRequestDTO" , "ocr_controller"]
