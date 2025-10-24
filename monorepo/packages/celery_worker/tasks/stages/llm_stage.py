"""LLM 분석 스테이지

OpenAI API를 사용하여 OCR 텍스트를 구조화된 데이터로 변환합니다.
"""

import json
from typing import Any, Dict

from shared.config import settings
from shared.pipeline.context import LLMResult, PipelineContext
from shared.pipeline.stage import PipelineStage


class LLMStage(PipelineStage):
    """LLM 분석 스테이지

    OCR로 추출된 텍스트를 LLM으로 분석하여 구조화된 데이터로 변환합니다.
    """

    def __init__(self):
        super().__init__()
        self.client = ""
        self.MODEL_SERVER_URL = settings.MODEL_SERVER_URL
        # TODO: API 키는 환경 변수에서 로드

    def validate_input(self, context: PipelineContext) -> None:
        """입력 검증: OCR 결과가 있는지 확인

        Args:
            context: 파이프라인 컨텍스트

        Raises:
            ValueError: OCR 결과가 없거나 텍스트가 없을 때
        """
        if not context.ocr_result:
            raise ValueError("OCR result is required for LLM analysis")

        if not context.ocr_result.bbox:
            raise ValueError("OCR bbox is empty")

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
        ocr_result = context.ocr_result
        if ocr_result is None:
            return context

        ocr_bbox = ocr_result.bbox

        # TODO: 실제 LLM API 호출 구현
        # 현재는 Mock 데이터 반환
        context.llm_result = LLMResult(
            analysis="Mock LLM analysis result",
            confidence=0.9,
            entities={
                "cr_number": "CR-2024-001",
                "title": "Sample CR",
                "description": "Sample description",
            },
            metadata={
                "model": "mock",
                "tokens_used": 0,
                "prompt": self._build_prompt(str(ocr_bbox), context.options),
            },
        )

        return context

    def _build_prompt(self, ocr_bbox: str, options: Dict[str, Any]) -> str:
        """LLM 프롬프트 생성

        Args:
            text: OCR로 추출된 텍스트
            options: 파이프라인 옵션

        Returns:
            LLM 프롬프트
        """
        _ = options  # 향후 사용 가능
        return f"""
Extract the following information from this CR document:

{ocr_bbox}

Extract:
- CR Number
- Title
- Description
- Requester
- Date
- Priority
- Status
- Changes requested

Return as JSON.
"""

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """LLM 응답 파싱

        Args:
            response: LLM 응답 (JSON 문자열)

        Returns:
            파싱된 딕셔너리

        Raises:
            ValueError: JSON 파싱 실패
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}") from e

    def validate_output(self, context: PipelineContext) -> None:
        """출력 검증: 필수 필드가 있는지 확인

        Args:
            context: 파이프라인 컨텍스트

        Raises:
            ValueError: LLM 결과가 없거나 필수 필드가 없을 때
        """
        if not context.llm_result:
            raise ValueError("LLM result is empty")

        if not context.llm_result.analysis:
            raise ValueError("LLM analysis is empty")

        # entities가 있는 경우 필수 필드 검증
        if context.llm_result.entities:
            required_fields = ["cr_number", "title", "description"]
            missing_fields = [
                field
                for field in required_fields
                if field not in context.llm_result.entities
            ]

            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
