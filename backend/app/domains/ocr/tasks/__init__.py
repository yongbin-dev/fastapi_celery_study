# app/domains/ocr/tasks/__init__.py
"""
OCR Celery 태스크
"""

from .ocr_tasks import extract_text_task

__all__ = ["extract_text_task"]
