# crud/__init__.py

"""
CRUD 모듈

각 모델에 대한 동기/비동기 CRUD 작업을 제공하는 클래스들을 포함합니다.

- sync_crud: SQLAlchemy Session을 사용하는 동기 CRUD 작업
- async_crud: SQLAlchemy AsyncSession을 사용하는 비동기 CRUD 작업
"""

# 동기 CRUD 가져오기 (기존 호환성 유지)
# 비동기 CRUD 가져오기 (async_ 접두사로 구분)
from .async_crud import (
    AsyncCRUDBase,
    AsyncCRUDChainExecution,
    AsyncCRUDOCRExecution,
    AsyncCRUDOCRTextBox,
    AsyncCRUDTaskLog,
)
from .async_crud import (
    chain_execution_crud as async_chain_execution_crud,
)
from .async_crud import (
    ocr_execution_crud as async_ocr_execution_crud,
)
from .async_crud import (
    ocr_text_box_crud as async_ocr_text_box_crud,
)
from .async_crud import (
    task_log_crud as async_task_log_crud,
)
from .sync_crud import (
    CRUDBase,
    CRUDChainExecution,
    CRUDOCRExecution,
    CRUDOCRTextBox,
    CRUDTaskLog,
    chain_execution_crud,
    ocr_execution_crud,
    ocr_text_box_crud,
    task_log_crud,
)

__all__ = [
    # 동기 Base CRUD classes
    "CRUDBase",
    # 동기 CRUD classes
    "CRUDChainExecution",
    "CRUDOCRExecution",
    "CRUDOCRTextBox",
    "CRUDTaskLog",
    # 동기 CRUD instances (ready to use)
    "chain_execution_crud",
    "ocr_execution_crud",
    "ocr_text_box_crud",
    "task_log_crud",
    # 비동기 Base CRUD classes
    "AsyncCRUDBase",
    # 비동기 CRUD classes
    "AsyncCRUDChainExecution",
    "AsyncCRUDOCRExecution",
    "AsyncCRUDOCRTextBox",
    "AsyncCRUDTaskLog",
    # 비동기 CRUD instances (ready to use)
    "async_chain_execution_crud",
    "async_ocr_execution_crud",
    "async_ocr_text_box_crud",
    "async_task_log_crud",
]
