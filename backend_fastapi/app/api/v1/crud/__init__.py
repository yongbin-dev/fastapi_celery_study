# crud/__init__.py

"""
CRUD 모듈

각 모델에 대한 동기/비동기 CRUD 작업을 제공하는 클래스들을 포함합니다.

- sync_crud: SQLAlchemy Session을 사용하는 동기 CRUD 작업
- async_crud: SQLAlchemy AsyncSession을 사용하는 비동기 CRUD 작업
"""

# 동기 CRUD 가져오기 (기존 호환성 유지)
from .sync_crud import (
    CRUDBase,
    CRUDBaseWithSoftDelete,
    CRUDChainExecution,
    CRUDTaskLog,
    CRUDTaskResult,
    CRUDTaskExecutionHistory,
    CRUDTaskMetadata,
    chain_execution,
    task_log,
    task_result,
    task_execution_history,
    task_metadata,
)

# 비동기 CRUD 가져오기 (async_ 접두사로 구분)
from .async_crud import (
    AsyncCRUDBase,
    AsyncCRUDBaseWithSoftDelete,
    AsyncCRUDChainExecution,
    AsyncCRUDTaskLog,
    AsyncCRUDTaskResult,
    AsyncCRUDTaskExecutionHistory,
    AsyncCRUDTaskMetadata,
    chain_execution as async_chain_execution,
    task_log as async_task_log,
    task_result as async_task_result,
    task_execution_history as async_task_execution_history,
    task_metadata as async_task_metadata,
)

__all__ = [
    # 동기 Base CRUD classes
    "CRUDBase",
    "CRUDBaseWithSoftDelete",
    # 동기 CRUD classes
    "CRUDChainExecution",
    "CRUDTaskLog",
    "CRUDTaskResult",
    "CRUDTaskExecutionHistory",
    "CRUDTaskMetadata",
    # 동기 CRUD instances (ready to use)
    "chain_execution",
    "task_log",
    "task_result",
    "task_execution_history",
    "task_metadata",
    # 비동기 Base CRUD classes
    "AsyncCRUDBase",
    "AsyncCRUDBaseWithSoftDelete",
    # 비동기 CRUD classes
    "AsyncCRUDChainExecution",
    "AsyncCRUDTaskLog",
    "AsyncCRUDTaskResult",
    "AsyncCRUDTaskExecutionHistory",
    "AsyncCRUDTaskMetadata",
    # 비동기 CRUD instances (ready to use)
    "async_chain_execution",
    "async_task_log",
    "async_task_result",
    "async_task_execution_history",
    "async_task_metadata",
]
