# app/domains/ocr/__init__.py
"""
OCR 도메인 모듈
"""

from .schemas import OCRRequestDTO, OCRResultDTO, TextBoxDTO

__all__ = ["OCRResultDTO", "TextBoxDTO", "OCRRequestDTO"]
