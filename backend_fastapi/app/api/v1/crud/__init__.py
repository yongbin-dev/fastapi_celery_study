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
    CRUDChainExecution,
    CRUDTaskLog,
    chain_execution,
    task_log,
)

# 비동기 CRUD 가져오기 (async_ 접두사로 구분)
from .async_crud import (
    AsyncCRUDBase,
    AsyncCRUDChainExecution,
    AsyncCRUDTaskLog,
    chain_execution as async_chain_execution,
    task_log as async_task_log,
)

__all__ = [
    # 동기 Base CRUD classes
    "CRUDBase",
    # 동기 CRUD classes
    "CRUDChainExecution",
    "CRUDTaskLog",
    # 동기 CRUD instances (ready to use)
    "chain_execution",
    "task_log",
    # 비동기 Base CRUD classes
    "AsyncCRUDBase",
    # 비동기 CRUD classes
    "AsyncCRUDChainExecution",
    "AsyncCRUDTaskLog",
    # 비동기 CRUD instances (ready to use)
    "async_chain_execution",
    "async_task_log",
]
