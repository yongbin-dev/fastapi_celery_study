import traceback

from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.logging import get_logger
from app.utils.response_builder import ResponseBuilder

logger = get_logger(__name__)


def setup_exception_handlers(app: FastAPI):
    """예외 핸들러 설정"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):

        logger.error(
            f"🔴 HTTP Exception | "
            f"Path: {request.url.path} | "
            f"Status: {exc.status_code} | "
            f"Detail: {exc.detail} | "
            f"Traceback: {traceback.format_exc()}"
        )

        # 상태 코드별 에러 코드 매핑
        error_code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            422: "UNPROCESSABLE_ENTITY",
            429: "TOO_MANY_REQUESTS",
            500: "INTERNAL_SERVER_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE",
        }

        error_response = ResponseBuilder.error(
            message=str(exc.detail),
            error_code=error_code_map.get(exc.status_code, "HTTP_ERROR"),
        )

        return JSONResponse(status_code=exc.status_code, content=error_response.dict())

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # logger.error(f"에러 발생: {traceback.format_exc()}")
        error_response = ResponseBuilder.error(
            message="서버 내부 오류가 발생했습니다", error_code="INTERNAL_SERVER_ERROR"
        )

        return JSONResponse(status_code=500, content=error_response.dict())

    logger.info("✅ 예외 핸들러 설정 완료")
