from typing import Any, Optional
from datetime import datetime
from app.models.response import ResponseStatus, PaginationMeta


class ResponseBuilder:
    @staticmethod
    def success(
            data: Any = None,
            message: str = "성공",
            meta: Optional[PaginationMeta] = None
    ) -> dict:
        """성공 응답 생성"""
        response = {
            "success": True,
            "status": ResponseStatus.SUCCESS.value,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

        if data is not None:
            response["data"] = data

        if meta:
            response["meta"] = meta.dict()

        return response

    @staticmethod
    def error(
            message: str = "오류가 발생했습니다",
            error_code: str = "UNKNOWN_ERROR",
            details: Any = None
    ) -> dict:
        """에러 응답 생성"""
        response = {
            "success": False,
            "status": ResponseStatus.ERROR.value,
            "message": message,
            "error_code": error_code,
            "timestamp": datetime.now().isoformat()
        }

        if details:
            response["details"] = details

        return response

    @staticmethod
    def paginated(
            data: list,
            page: int,
            size: int,
            total: int,
            message: str = "성공"
    ) -> dict:
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

        return ResponseBuilder.success(data=data, message=message, meta=meta)