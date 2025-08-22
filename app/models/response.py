from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

T = TypeVar('T')


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class BaseResponse(BaseModel, Generic[T]):
    success: bool
    status: ResponseStatus
    message: str
    data: Optional[T] = None
    error_code: Optional[str] = None
    timestamp: str

    class Config:
        use_enum_values = True


class PaginationMeta(BaseModel):
    page: int
    size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseResponse[T]):
    meta: Optional[PaginationMeta] = None
