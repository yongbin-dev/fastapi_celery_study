# app/core/__init__.py
"""
Core utilities for the API server
"""

from .auto_router import AutoRouter, setup_auto_routers

__all__ = ["AutoRouter", "setup_auto_routers"]
