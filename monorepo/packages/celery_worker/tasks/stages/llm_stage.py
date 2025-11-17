"""LLM 분석 스테이지

OpenAI API를 사용하여 OCR 텍스트를 구조화된 데이터로 변환합니다.
"""

import json

from shared.config import settings
from shared.core.logging import get_logger
from shared.pipeline.context import LLMResult, PipelineContext
from shared.pipeline.stage import PipelineStage

from tasks.client.llm_client import LLMClient

logger = get_logger(__name__)


class LLMStage(PipelineStage):
    """LLM 분석 스테이지

    OCR로 추출된 텍스트를 LLM으로 분석하여 구조화된 데이터로 변환합니다.
    """

    def __init__(self):
        super().__init__()
        self.MODEL_SERVER_URL = settings.MODEL_SERVER_URL
        self.client = LLMClient(server_url="http://192.168.0.122:38000/v1")
        # TODO: API 키는 환경 변수에서 로드

    def validate_input(self, context: PipelineContext) -> None:
        """입력 검증: OCR 결과가 있는지 확인

        Args:
            context: 파이프라인 컨텍스트

        Raises:
            ValueError: OCR 결과가 없거나 텍스트가 없을 때
        """
        if not context.ocr_results:
            raise ValueError("OCR result is required for LLM analysis")

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """LLM으로 텍스트 구조화

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            업데이트된 컨텍스트 (llm_result 포함)

        Raises:
            RetryableError: API 오류 또는 Rate limit
        """
        # OCR 텍스트 추출
        ocr_results = context.ocr_results
        if ocr_results is None:
            return context

        # OCR 결과를 딕셔너리로 변환
        messages = [msg.model_dump() for msg in ocr_results]

        # LLM 메시지 구성 (content는 반드시 문자열이어야 함)
        llm_messages = []
        llm_messages.append(
            {
                "role": "system",
                "content": (
                    "ocr 모델을 돌려서 나온 text_boxes로 나온 결과야 텍스트 박스 "
                    "중 숫자만 추출해서 알려줘."
                ),
            }
        )
        # 딕셔너리를 JSON 문자열로 변환하여 전달
        llm_messages.append(
            {"role": "user", "content": json.dumps(messages, ensure_ascii=False)}
        )

        result = await self.client.chat_completion(messages=llm_messages)

        context.llm_result = LLMResult(
            entities=result,
            metadata={
                "model": "mock",
                "tokens_used": 0,
            },
        )

        return context

    def validate_output(self, context: PipelineContext) -> None:
        """출력 검증: 필수 필드가 있는지 확인

        Args:
            context: 파이프라인 컨텍스트

        Raises:
            ValueError: LLM 결과가 없거나 필수 필드가 없을 때
        """
        pass
        # if not context.llm_result:
        #     raise ValueError("LLM result is empty")

        # if not context.llm_result.analysis:
        #     raise ValueError("LLM analysis is empty")

        # # entities가 있는 경우 필수 필드 검증
        # if context.llm_result.entities:
        #     required_fields = ["cr_number", "title", "description"]
        #     missing_fields = [
        #         field
        #         for field in required_fields
        #         if field not in context.llm_result.entities
        #     ]

        #     if missing_fields:
        #         raise ValueError(f"Missing required fields: {missing_fields}")

    def save_db(self, context: PipelineContext):
        pass
