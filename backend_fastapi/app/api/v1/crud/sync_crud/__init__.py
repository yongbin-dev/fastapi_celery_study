# crud/sync_crud/__init__.py

"""
동기 CRUD 모듈

SQLAlchemy Session을 사용하는 동기 CRUD 작업을 제공합니다.
"""

from .base import CRUDBase, CRUDBaseWithSoftDelete
from .chain_execution import CRUDChainExecution, chain_execution
from .task_log import CRUDTaskLog, task_log
from .task_result import CRUDTaskResult, task_result
from .task_execution_history import CRUDTaskExecutionHistory, task_execution_history
from .task_metadata import CRUDTaskMetadata, task_metadata

__all__ = [
    # Base CRUD classes
    "CRUDBase",
    "CRUDBaseWithSoftDelete",
    # CRUD classes
    "CRUDChainExecution",
    "CRUDTaskLog",
    "CRUDTaskResult",
    "CRUDTaskExecutionHistory",
    "CRUDTaskMetadata",
    # CRUD instances (ready to use)
    "chain_execution",
    "task_log",
    "task_result",
    "task_execution_history",
    "task_metadata",
]
