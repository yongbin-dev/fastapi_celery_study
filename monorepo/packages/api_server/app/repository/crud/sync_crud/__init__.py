# crud/sync_crud/__init__.py

"""
동기 CRUD 모듈

SQLAlchemy Session을 사용하는 동기 CRUD 작업을 제공합니다.
"""

from .base import CRUDBase
from .chain_execution import CRUDChainExecution, chain_execution_crud
from .ocr_execution import CRUDOCRExecution, ocr_execution_crud
from .ocr_text_box import CRUDOCRTextBox, ocr_text_box_crud
from .task_log import CRUDTaskLog, task_log_crud

__all__ = [
    # Base CRUD classes
    "CRUDBase",
    # CRUD classes
    "CRUDChainExecution",
    "CRUDOCRExecution",
    "CRUDOCRTextBox",
    "CRUDTaskLog",
    # CRUD instances (ready to use)
    "chain_execution_crud",
    "ocr_execution_crud",
    "ocr_text_box_crud",
    "task_log_crud",
]
