# app/core/__init__.py
"""
Core utilities for the API server
"""

from .auto_router import AutoRouter, setup_auto_routers
from .logging import get_logger
from .database import get_db

__all__ = ["AutoRouter", "setup_auto_routers"  , "get_logger" , "get_db"]
