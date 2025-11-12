"""파이프라인 처리 모듈

단일/배치 이미지 처리를 위한 파이프라인 실행 함수

Public API:
    - execute_batch_ocr_pipeline: 배치 OCR 파이프라인 실행

Deprecated:
    - single_ocr.py: Chain 기반 단일 파이프라인 (참고용)
"""

from .batch_ocr import execute_batch_ocr_pipeline

__all__ = [
    "execute_batch_ocr_pipeline",
]
