# app/exceptions/user_exceptions.py

from typing import Optional, Dict, Any
from .base import BaseBusinessException


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