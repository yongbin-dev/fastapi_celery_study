"""PipelineStage - 파이프라인 스테이지 추상 기본 클래스

각 스테이지(OCR, LLM, Layout, Excel)의 기본 구조를 정의합니다.
"""

from abc import ABC, abstractmethod

from celery.beat import get_logger

from .context import PipelineContext

logger = get_logger(__name__)


class PipelineStage(ABC):
    """파이프라인 스테이지 추상 기본 클래스

    모든 스테이지는 이 클래스를 상속받아 execute 메서드를 구현해야 합니다.

    Attributes:
        stage_name: 스테이지 이름
    """

    def __init__(self):
        self.stage_name = self.__class__.__name__

    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """실제 처리 로직 (서브클래스에서 구현 필수)

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            업데이트된 컨텍스트

        Raises:
            ValueError: 처리 중 오류 발생 시
        """
        pass

    def validate_input(self, context: PipelineContext) -> None:
        """입력 데이터 검증

        Args:
            context: 파이프라인 컨텍스트

        Raises:
            ValueError: 입력 데이터가 유효하지 않을 때
        """
        _ = context  # 서브클래스에서 구현

    def validate_output(self, context: PipelineContext) -> None:
        """출력 데이터 검증

        Args:
            context: 파이프라인 컨텍스트

        Raises:
            ValueError: 출력 데이터가 유효하지 않을 때
        """
        _ = context  # 서브클래스에서 구현

    def save_db(self, context: PipelineContext) -> None:
        """DB 저장

        Args:
            context: 파이프라인 컨텍스트


        """
        _ = context  # 서브클래스에서 구현

    async def run(self, context: PipelineContext) -> PipelineContext:
        """전체 실행 플로우 (템플릿 메서드 패턴)

        1. 입력 검증
        2. 실행
        3. 출력 검증
        4. 상태 업데이트

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            업데이트된 컨텍스트

        Raises:
            Exception: 실행 중 오류 발생 시
        """
        try:
            # 1. 입력 검증
            self.validate_input(context)

            # 2. 실행
            context.update_status(
                status=f"{self.stage_name.lower()}_in_progress", stage=self.stage_name
            )
            context = await self.execute(context)
            logger.info(f"{self.stage_name.lower()}_in_progress 실행")
            # 3. 출력 검증
            self.validate_output(context)

            logger.info(f"{self.stage_name.lower()}_in_progress 검증 성공")
            # 4. 상태 업데이트
            context.update_status(
                status=f"{self.stage_name.lower()}_completed", stage=self.stage_name
            )

            self.save_db(context)

            logger.info(f"{self.stage_name.lower()}_in_progress 상태 업데이트")
            return context

        except Exception as e:
            # 에러 처리
            context.error = str(e)
            context.status = "failed"
            context.current_stage = self.stage_name
            raise
