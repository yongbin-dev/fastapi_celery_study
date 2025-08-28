from typing import Any, Optional

class BaseCustomException(Exception):
    """기본 커스텀 예외"""
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str,
        details: Optional[Any] = None
    ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(message)

class ValidationError(BaseCustomException):
    def __init__(self, message: str = "유효성 검사 실패", details: Optional[Any] = None):
        super().__init__(400, message, "VALIDATION_ERROR", details)

class NotFoundError(BaseCustomException):
    def __init__(self, message: str = "리소스를 찾을 수 없습니다"):
        super().__init__(404, message, "NOT_FOUND")

class UnauthorizedError(BaseCustomException):
    def __init__(self, message: str = "인증이 필요합니다"):
        super().__init__(401, message, "UNAUTHORIZED")

class ForbiddenError(BaseCustomException):
    def __init__(self, message: str = "권한이 없습니다"):
        super().__init__(403, message, "FORBIDDEN")

class InternalServerError(BaseCustomException):
    def __init__(self, message: str = "서버 내부 오류가 발생했습니다"):
        super().__init__(500, message, "INTERNAL_SERVER_ERROR")