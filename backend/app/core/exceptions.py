# app/core/exceptions.py

from abc import ABC
from typing import Optional, Dict, Any
from fastapi import HTTPException


class BaseBusinessException(Exception, ABC):
    """비즈니스 예외의 기본 클래스"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
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
            "details": self.details,
        }

    def __str__(self) -> str:
        return f"{self.error_code}: {self.message}"


# Celery 전용 예외 클래스들


class BaseCeleryException(Exception, ABC):
    """Celery 태스크 예외의 기본 클래스"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        task_id: Optional[str] = None,
        chain_id: Optional[str] = None,
        stage_num: Optional[int] = None,
        retry_count: int = 0,
        max_retries: int = 3,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.task_id = task_id
        self.chain_id = chain_id
        self.stage_num = stage_num
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "task_id": self.task_id,
            "chain_id": self.chain_id,
            "stage_num": self.stage_num,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "details": self.details,
        }

    def __str__(self) -> str:
        context = (
            f"task_id={self.task_id}, chain_id={self.chain_id}, stage={self.stage_num}"
        )
        return f"{self.error_code}: {self.message} ({context})"


class TaskValidationError(BaseCeleryException):
    """태스크 입력 데이터 검증 오류"""

    pass


class TaskTimeoutError(BaseCeleryException):
    """태스크 타임아웃 오류"""

    pass


class TaskResourceError(BaseCeleryException):
    """태스크 리소스 부족 오류 (메모리, CPU 등)"""

    pass


class PipelineStageError(BaseCeleryException):
    """파이프라인 스테이지 처리 오류"""

    pass


class TaskRetryExhaustedError(BaseCeleryException):
    """재시도 횟수 초과 오류"""

    pass


class ChainExecutionError(BaseCeleryException):
    """체인 실행 전체 오류"""

    pass


class ModelLoadingError(BaseCeleryException):
    """AI 모델 로딩 오류"""

    pass


class DataProcessingError(BaseCeleryException):
    """데이터 처리 오류"""

    pass
