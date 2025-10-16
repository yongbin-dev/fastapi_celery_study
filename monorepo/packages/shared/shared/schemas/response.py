from enum import Enum
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


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

    model_config = {"use_enum_values": True}


class PaginationMeta(BaseModel):
    page: int
    size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseResponse[T]):
    meta: Optional[PaginationMeta] = None
