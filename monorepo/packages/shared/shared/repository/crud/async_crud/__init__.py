# crud/async_crud/__init__.py

"""
비동기 CRUD 모듈

SQLAlchemy AsyncSession을 사용하는 비동기 CRUD 작업을 제공합니다.
"""

from .base import AsyncCRUDBase
from .batch_execution import (
    AsyncCRUDBatchExecution,
    async_batch_execution_crud,
)
from .chain_execution import AsyncCRUDChainExecution, chain_execution_crud
from .ocr_execution import AsyncCRUDOCRExecution, ocr_execution_crud
from .ocr_text_box import AsyncCRUDOCRTextBox, ocr_text_box_crud
from .task_log import AsyncCRUDTaskLog, task_log_crud

__all__ = [
    # Base CRUD classes
    "AsyncCRUDBase",
    # CRUD classes
    "AsyncCRUDBatchExecution",
    "AsyncCRUDChainExecution",
    "AsyncCRUDOCRExecution",
    "AsyncCRUDTaskLog",
    "AsyncCRUDOCRTextBox",
    # CRUD instances (ready to use)
    "async_batch_execution_crud",
    "chain_execution_crud",
    "ocr_execution_crud",
    "ocr_text_box_crud",
    "task_log_crud",
]
