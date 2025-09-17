from typing import Any, Optional
from datetime import datetime

from app.schemas.common import ApiResponse
from app.schemas.response import ResponseStatus, PaginationMeta


class ResponseBuilder:
    @staticmethod
    def success(
            data: Any = None,
            message: str = "성공",
            meta: Optional[PaginationMeta] = None
    ) -> ApiResponse:
        """성공 응답 생성"""

        response = ApiResponse(
            success=True,
            status=ResponseStatus.SUCCESS.value,
            message=message,
            timestamp=datetime.now().isoformat(),
            data=data,
        )

        return response

    @staticmethod
    def error(
            message: str = "오류가 발생했습니다",
            error_code: str = "UNKNOWN_ERROR",
            details: Any = None
    ) -> ApiResponse:
        """에러 응답 생성"""
        response = ApiResponse(
            success=False,
            status=ResponseStatus.ERROR.value,
            message=message,
            timestamp=datetime.now().isoformat(),
            data=None,
            error_code=error_code,
            details=details
        )

        return response

    @staticmethod
    def paginated(
            data: list,
            page: int,
            size: int,
            total: int,
            message: str = "성공"
    ) -> ApiResponse:
        """페이지네이션 응답 생성"""
        total_pages = (total + size - 1) // size

        meta = PaginationMeta(
            page=page,
            size=size,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )

        response = ApiResponse(
            success=True,
            status=ResponseStatus.SUCCESS.value,
            message=message,
            timestamp=datetime.now().isoformat(),
            data=data,
            meta=meta
        )

        return response
