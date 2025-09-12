# app/core/exceptions.py

from abc import ABC
from typing import Optional, Dict, Any
from fastapi import HTTPException


class BaseBusinessException(Exception, ABC):
    """비즈니스 예외의 기본 클래스"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = None,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details
        }
    
    def __str__(self) -> str:
        return f"{self.error_code}: {self.message}"


class CustomHTTPException(HTTPException):
    """커스텀 HTTP 예외 클래스"""
    
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(status_code, detail, headers)
        self.error_code = error_code


# ===== 일반적인 예외들 =====

class ValidationError(BaseBusinessException):
    def __init__(self, message: str = "유효성 검사 실패", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", 400, details)


class NotFoundError(BaseBusinessException):
    def __init__(self, message: str = "리소스를 찾을 수 없습니다"):
        super().__init__(message, "NOT_FOUND", 404)


class UnauthorizedError(BaseBusinessException):
    def __init__(self, message: str = "인증이 필요합니다"):
        super().__init__(message, "UNAUTHORIZED", 401)


class ForbiddenError(BaseBusinessException):
    def __init__(self, message: str = "권한이 없습니다"):
        super().__init__(message, "FORBIDDEN", 403)


class InternalServerError(BaseBusinessException):
    def __init__(self, message: str = "서버 내부 오류가 발생했습니다"):
        super().__init__(message, "INTERNAL_SERVER_ERROR", 500)


# ===== 사용자 관련 예외들 =====

class UserServiceException(BaseBusinessException):
    """사용자 서비스 관련 기본 예외"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="USER_SERVICE_ERROR",
            status_code=500,
            details=details
        )


class UserNotFoundException(BaseBusinessException):
    """사용자를 찾을 수 없을 때 발생하는 예외"""
    
    def __init__(self, user_id: Optional[int] = None, email: Optional[str] = None, username: Optional[str] = None):
        identifier = user_id or email or username or "unknown"
        message = f"사용자를 찾을 수 없습니다: {identifier}"
        
        super().__init__(
            message=message,
            error_code="USER_NOT_FOUND",
            status_code=404,
            details={
                "user_id": user_id,
                "email": email, 
                "username": username
            }
        )


class UserAlreadyExistsException(BaseBusinessException):
    """사용자가 이미 존재할 때 발생하는 예외"""
    
    def __init__(self, field: str, value: str):
        message = f"이미 사용 중인 {field}입니다: {value}"
        
        super().__init__(
            message=message,
            error_code="USER_ALREADY_EXISTS",
            status_code=400,
            details={
                "field": field,
                "value": value
            }
        )


class UserEmailAlreadyExistsException(UserAlreadyExistsException):
    """이메일이 이미 존재할 때 발생하는 예외"""
    
    def __init__(self, email: str):
        super().__init__(field="이메일", value=email)
        self.error_code = "USER_EMAIL_ALREADY_EXISTS"


class UserUsernameAlreadyExistsException(UserAlreadyExistsException):
    """사용자명이 이미 존재할 때 발생하는 예외"""
    
    def __init__(self, username: str):
        super().__init__(field="사용자명", value=username)
        self.error_code = "USER_USERNAME_ALREADY_EXISTS"


class DatabaseConnectionException(BaseBusinessException):
    """데이터베이스 연결 관련 예외"""
    
    def __init__(self, message: str = "데이터베이스 연결에 실패했습니다"):
        super().__init__(
            message=message,
            error_code="DATABASE_CONNECTION_ERROR", 
            status_code=503,
            details={}
        )