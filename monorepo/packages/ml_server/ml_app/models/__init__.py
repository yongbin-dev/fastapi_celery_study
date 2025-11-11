"""Models package for celery_worker"""

from .ocr_model import OCRModel, get_ocr_model

__all__ = ["OCRModel", "get_ocr_model"]
