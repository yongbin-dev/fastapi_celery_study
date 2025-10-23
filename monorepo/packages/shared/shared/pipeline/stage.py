"""PipelineStage - 파이프라인 스테이지 추상 기본 클래스

각 스테이지(OCR, LLM, Layout, Excel)의 기본 구조를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Any
from .context import PipelineContext


class PipelineStage(ABC):
    """파이프라인 스테이지 추상 기본 클래스

    모든 스테이지는 이 클래스를 상속받아 execute 메서드를 구현해야 합니다.

    Attributes:
        stage_name: 스테이지 이름
    """

    def __init__(self, stage_name: str):
        self.stage_name = stage_name

    @abstractmethod
    async def execute(self, context: PipelineContext) -> Any:
        """스테이지 실행

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            스테이지 실행 결과

        Raises:
            StageError: 스테이지 실행 중 오류 발생 시
        """
        pass

    async def pre_execute(self, context: PipelineContext) -> None:
        """스테이지 실행 전 처리 (선택적)"""
        pass

    async def post_execute(self, context: PipelineContext, result: Any) -> None:
        """스테이지 실행 후 처리 (선택적)"""
        pass

    def validate_input(self, context: PipelineContext) -> bool:
        """입력 데이터 검증 (선택적)

        Returns:
            검증 성공 여부
        """
        return True
