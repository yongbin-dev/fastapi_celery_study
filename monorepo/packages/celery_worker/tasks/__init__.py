"""Celery 태스크 진입점

이 파일은 모든 주요 태스크 함수들의 진입점 역할을 합니다.
API 서버 등 외부 패키지에서 쉽게 import할 수 있도록 구성되었습니다.

"""

# ============================================================================
# 배치 처리 태스크 (Batch Processing)
# ============================================================================

from .batch import (
    # Celery Tasks
    process_image_chunk_task,  # 이미지 청크 처리 태스크
    # Public API Functions
    start_image_batch_pipeline,  # 이미지 배치 파이프라인 시작
)

# ============================================================================
# 파이프라인 실행 함수 (Pipeline Execution)
# ============================================================================
from .pipeline import (
    execute_batch_ocr_pipeline,  # 배치 OCR 파이프라인 직접 실행
)

# ============================================================================
# Public API
# ============================================================================

__all__ = [
    # Batch Processing - Public APIs
    "start_image_batch_pipeline",
    # Batch Processing - Celery Tasks
    "process_image_chunk_task",
    # Pipeline Execution
    "execute_batch_ocr_pipeline",
]
