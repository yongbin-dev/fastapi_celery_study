# app/core/__init__.py
"""
Core utilities for the API server
"""

from .database import get_db
from .logging import get_logger

# FastAPI 관련 모듈은 선택적으로 import (celery_worker에서는 불필요)
try:
    from .auto_router import AutoRouter, setup_auto_routers

    __all__ = ["AutoRouter", "setup_auto_routers", "get_logger", "get_db"]
except ImportError:
    # FastAPI가 없는 환경 (예: celery_worker)
    __all__ = ["get_logger", "get_db"]
