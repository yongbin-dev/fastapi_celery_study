"""LLM Stage - LLM 분석 로직

OCR로 추출한 텍스트를 LLM으로 분석하는 스테이지입니다.
"""

from typing import Any

from shared.core.logging import get_logger
from shared.pipeline import PipelineContext, PipelineStage
from shared.pipeline.exceptions import StageError

logger = get_logger(__name__)

class LLMStage(PipelineStage):
    """LLM 분석 스테이지

    OCR 결과를 LLM으로 분석합니다.
    """

    def __init__(self):
        super().__init__(stage_name="llm")

    async def execute(self, context: PipelineContext) -> Any:
        """LLM 분석 실행

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            LLM 분석 결과

        Raises:
            StageError: LLM 분석 중 오류 발생 시
        """
        try:
            logger.info(f"LLM 분석 시작: {context.context_id}")

            # OCR 결과 가져오기
            ocr_result = context.get_stage_data("ocr")
            if not ocr_result:
                raise StageError(
                    stage_name=self.stage_name,
                    message="OCR 결과를 찾을 수 없습니다"
                )

            # TODO: 실제 LLM 분석 로직 구현
            # 1. OCR 결과에서 텍스트 추출
            # 2. LLM API 호출
            # 3. 분석 결과 반환

            # 임시 구현
            result = {
                "analysis": "",
                "entities": []
            }

            logger.info(f"LLM 분석 완료: {context.context_id}")
            return result

        except Exception as e:
            logger.error(f"LLM 분석 에러: {str(e)}")
            raise StageError(
                stage_name=self.stage_name,
                message=f"LLM 분석 실패: {str(e)}"
            ) from e

    def validate_input(self, context: PipelineContext) -> bool:
        """입력 검증

        OCR 결과가 컨텍스트에 존재하는지 확인합니다.
        """
        ocr_result = context.get_stage_data("ocr")
        return ocr_result is not None
