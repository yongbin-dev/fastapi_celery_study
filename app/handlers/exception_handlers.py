# app/handlers/exception_handlers.py

import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from ..core.exceptions import BaseCustomException
from ..utils.response_builder import ResponseBuilder


logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI):
    """예외 핸들러 설정"""

    @app.exception_handler(BaseCustomException)
    async def custom_exception_handler(request: Request, exc: BaseCustomException):
        logger.error(
            f"🔴 Custom Exception | "
            f"Path: {request.url.path} | "
            f"Code: {exc.error_code} | "
            f"Message: {exc.message}"
        )

        error_response = ResponseBuilder.error(
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(
            f"🔴 HTTP Exception | "
            f"Path: {request.url.path} | "
            f"Status: {exc.status_code} | "
            f"Detail: {exc.detail}"
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
            503: "SERVICE_UNAVAILABLE"
        }

        error_response = ResponseBuilder.error(
            message=str(exc.detail),
            error_code=error_code_map.get(exc.status_code, "HTTP_ERROR")
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(
            f"🔴 Validation Error | "
            f"Path: {request.url.path} | "
            f"Errors: {len(exc.errors())} | "
            f"Details: {exc.errors()}"
        )

        error_details = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            error_details.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input")  # 입력값도 포함
            })

        error_response = ResponseBuilder.error(
            message="입력값 검증 실패",
            error_code="VALIDATION_ERROR",
            details=error_details
        )

        return JSONResponse(
            status_code=422,
            content=error_response
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """예상치 못한 모든 에러 처리"""
        logger.error(
            f"🔴 Unexpected Error | "
            f"Path: {request.url.path} | "
            f"Type: {type(exc).__name__} | "
            f"Message: {str(exc)}",
            exc_info=True  # 스택 트레이스 포함
        )

        error_response = ResponseBuilder.error(
            message="서버 내부 오류가 발생했습니다",
            error_code="INTERNAL_SERVER_ERROR"
        )

        return JSONResponse(
            status_code=500,
            content=error_response
        )

    logger.info("✅ 예외 핸들러 설정 완료")