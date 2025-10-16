# app/domains/ocr/__init__.py
"""
OCR 도메인 모듈
"""

from .controllers.ocr_controller import router as ocr_controller
from .schemas import OCRRequestDTO, OCRResultDTO, TextBoxDTO

__all__ = ["OCRResultDTO", "TextBoxDTO", "OCRRequestDTO" , "ocr_controller"]
