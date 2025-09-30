# app/schemas/common.py

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

from app.schemas.response import PaginationMeta

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """표준 API 응답 형식"""

    success: bool
    message: str
    status: str
    timestamp: str
    meta: Optional[PaginationMeta] = None
    data: Any
    error_code: Optional[str] = None
    details: Optional[dict[str, Any]] = None
