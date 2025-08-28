# app/exceptions/base.py

from abc import ABC
from typing import Optional, Dict, Any


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