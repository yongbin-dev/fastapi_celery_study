# app/domains/ocr/__init__.py
"""
OCR 도메인 모듈
"""
from .schemas import OCRResultDTO, TextBoxDTO, OCRRequestDTO

__all__ = ["OCRResultDTO", "TextBoxDTO", "OCRRequestDTO"]