from fastapi import FastAPI, Request
from app.core.logging import get_logger

logger = get_logger(__name__)

from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import BaseBusinessException, BaseCeleryException
from app.utils.response_builder import ResponseBuilder
from starlette.responses import JSONResponse
import traceback


def setup_exception_handlers(app: FastAPI):
    """예외 핸들러 설정"""

    @app.exception_handler(BaseCeleryException)
    async def celery_exception_handler(request: Request, exc: BaseCeleryException):
        logger.error(
            f"🔴 Celery Exception | "
            f"Path: {request.url.path} | "
            f"TaskID: {exc.task_id} | "
            f"ChainID: {exc.chain_id} | "
            f"Stage: {exc.stage_num} | "
            f"Code: {exc.error_code} | "
            f"Message: {exc.message} | "
            f"Retry: {exc.retry_count}/{exc.max_retries}"
        )

        error_response = ResponseBuilder.error(
            message=f"태스크 처리 중 오류가 발생했습니다: {exc.message}",
            error_code=exc.error_code,
            details={
                "task_context": {
                    "task_id": exc.task_id,
                    "chain_id": exc.chain_id,
                    "stage_num": exc.stage_num,
                    "retry_count": exc.retry_count,
                    "max_retries": exc.max_retries,
                },
                **exc.details,
            },
        )

        return JSONResponse(
            status_code=500, content=error_response.dict()  # Celery 에러는 일반적으로 서버 에러로 처리
        )

    @app.exception_handler(BaseBusinessException)
    async def business_exception_handler(request: Request, exc: BaseBusinessException):
        logger.error(
            f"🔴 Custom Exception | "
            f"Path: {request.url.path} | "
            f"Code: {exc.error_code} | "
            f"Message: {exc.message}"
        )

        error_response = ResponseBuilder.error(
            message=exc.message, error_code=exc.error_code, details=exc.details
        )

        return JSONResponse(status_code=exc.status_code, content=error_response.dict())

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(f"에러 발생: {traceback.format_exc()}")

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
            503: "SERVICE_UNAVAILABLE",
        }

        error_response = ResponseBuilder.error(
            message=str(exc.detail),
            error_code=error_code_map.get(exc.status_code, "HTTP_ERROR"),
        )

        return JSONResponse(status_code=exc.status_code, content=error_response.dict())

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"에러 발생: {traceback.format_exc()}")
        error_response = ResponseBuilder.error(
            message="서버 내부 오류가 발생했습니다", error_code="INTERNAL_SERVER_ERROR"
        )

        return JSONResponse(status_code=500, content=error_response.dict())

    logger.info("✅ 예외 핸들러 설정 완료")
