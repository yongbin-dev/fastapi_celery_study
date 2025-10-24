"""레이아웃 분석 스테이지

OCR의 bounding box 정보를 분석하여 테이블 구조를 파악합니다.
"""

# from typing import Any, Dict, List
# from shared.pipeline.context import PipelineContext
from shared.pipeline.stage import PipelineStage


class LayoutStage(PipelineStage):
    pass

    #     """출력 검증

    #     Args:
    #         context: 파이프라인 컨텍스트

    #     Raises:
    #         ValueError: 레이아웃 결과가 없을 때
    #     """
    #     if not context.layout_result:
    #         raise ValueError("Layout result is empty")
