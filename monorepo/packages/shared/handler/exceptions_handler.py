from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from ..core.logging import get_logger
from ..utils.response_builder import ResponseBuilder

logger = get_logger(__name__)


async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""

    # DEBUG 레벨에서만 상세 에러 정보 노출
    from shared.config import settings

    details = str(exc) if settings.DEBUG else None

    error_response = ResponseBuilder.error(
        message="서버 내부 오류가 발생했습니다",
        error_code="INTERNAL_SERVER_ERROR",
        details=details,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",  # noqa: E501
            "Access-Control-Allow-Headers": "*",
        },
    )


def setup_exception_handlers(app: FastAPI):
    """예외 핸들러 설정"""
    # 핸들러 등록
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("✅ 예외 핸들러 설정 완료")
