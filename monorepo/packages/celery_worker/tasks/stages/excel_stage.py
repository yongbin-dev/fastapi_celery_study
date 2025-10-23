"""Excel Stage - Excel 파일 생성 로직

분석 결과를 Excel 파일로 생성하는 스테이지입니다.
"""

from typing import Any

from shared.core.logging import get_logger
from shared.pipeline import PipelineContext, PipelineStage
from shared.pipeline.exceptions import StageError

logger = get_logger(__name__)

class ExcelStage(PipelineStage):
    """Excel 생성 스테이지

    파이프라인 결과를 Excel 파일로 생성합니다.
    """

    def __init__(self):
        super().__init__(stage_name="excel")

    async def execute(self, context: PipelineContext) -> Any:
        """Excel 생성 실행

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            Excel 파일 정보 (경로, URL 등)

        Raises:
            StageError: Excel 생성 중 오류 발생 시
        """
        try:
            logger.info(f"Excel 생성 시작: {context.context_id}")

            # 이전 스테이지 결과 가져오기
            ocr_result = context.get_stage_data("ocr")
            llm_result = context.get_stage_data("llm")
            layout_result = context.get_stage_data("layout")

            if not all([ocr_result, llm_result, layout_result]):
                raise StageError(
                    stage_name=self.stage_name,
                    message="이전 스테이지 결과를 찾을 수 없습니다"
                )

            # TODO: 실제 Excel 생성 로직 구현
            # 1. 분석 결과를 Excel 포맷으로 변환
            # 2. Excel 파일 생성
            # 3. Supabase Storage에 업로드
            # 4. 파일 정보 DB 저장

            # 임시 구현
            result = {
                "file_path": "",
                "file_url": "",
                "file_size": 0
            }

            logger.info(f"Excel 생성 완료: {context.context_id}")
            return result

        except Exception as e:
            logger.error(f"Excel 생성 에러: {str(e)}")
            raise StageError(
                stage_name=self.stage_name,
                message=f"Excel 생성 실패: {str(e)}"
            ) from e

    def validate_input(self, context: PipelineContext) -> bool:
        """입력 검증

        모든 이전 스테이지 결과가 존재하는지 확인합니다.
        """
        ocr_result = context.get_stage_data("ocr")
        llm_result = context.get_stage_data("llm")
        layout_result = context.get_stage_data("layout")

        return all([ocr_result, llm_result, layout_result])
