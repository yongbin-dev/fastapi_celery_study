# app/exceptions/handlers.py

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .base import BaseBusinessException
from ..utils.response_builder import ResponseBuilder
import logging

logger = logging.getLogger(__name__)


async def business_exception_handler(request: Request, exc: BaseBusinessException) -> JSONResponse:
    """비즈니스 예외 핸들러"""
    
    # 로그 기록
    logger.warning(f"Business exception occurred: {exc.error_code} - {exc.message}", extra={
        "error_code": exc.error_code,
        "status_code": exc.status_code,
        "details": exc.details,
        "path": request.url.path
    })
    
    # 표준화된 에러 응답 반환
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseBuilder.error(
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details
        ).dict()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """일반 예외 핸들러"""
    
    # 로그 기록
    logger.error(f"Unhandled exception occurred: {str(exc)}", extra={
        "exception_type": type(exc).__name__,
        "path": request.url.path
    }, exc_info=True)
    
    # 내부 서버 오류로 처리
    return JSONResponse(
        status_code=500,
        content=ResponseBuilder.error(
            message="내부 서버 오류가 발생했습니다",
            error_code="INTERNAL_SERVER_ERROR",
            details={"exception_type": type(exc).__name__}
        ).dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTPException 핸들러 (기존 FastAPI 예외와의 호환성)"""
    
    logger.warning(f"HTTP exception occurred: {exc.status_code} - {exc.detail}", extra={
        "status_code": exc.status_code,
        "detail": exc.detail,
        "path": request.url.path
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseBuilder.error(
            message=exc.detail,
            error_code="HTTP_ERROR",
            details={"status_code": exc.status_code}
        ).dict()
    )