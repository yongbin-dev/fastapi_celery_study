"""OCR 처리 스테이지

ML 서버를 호출하여 이미지/PDF 파일에서 텍스트를 추출합니다.
"""

import httpx
from app.domains.ocr.schemas.response import OCRResultDTO
from celery.beat import get_logger
from shared.config import settings
from shared.core.database import get_db_manager
from shared.pipeline.context import OCRResult, PipelineContext
from shared.pipeline.exceptions import RetryableError
from shared.pipeline.stage import PipelineStage
from shared.repository.crud.sync_crud import ocr_execution_crud, ocr_text_box_crud
from shared.schemas import OCRExecutionCreate
from shared.schemas.ocr_db import OCRTextBoxCreate

logger = get_logger(__name__)


class OCRStage(PipelineStage):
    """OCR 처리 스테이지

    ML 서버의 OCR 엔진을 사용하여 텍스트를 추출합니다.
    """

    def __init__(self):
        super().__init__()
        self.ml_server_url = settings.MODEL_SERVER_URL

    def validate_input(self, context: PipelineContext) -> None:
        """입력 검증: 파일 경로가 있는지 확인

        Args:
            context: 파이프라인 컨텍스트

        Raises:
            ValueError: 입력 파일 경로가 없을 때
        """
        if not context.input_file_path:
            raise ValueError("input_file_path is required")

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """ML 서버에 OCR 요청

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            업데이트된 컨텍스트 (ocr_result 포함)

        Raises:
            RetryableError: 네트워크 오류 또는 서버 오류
            ValueError: 클라이언트 오류
        """
        try:
            # ML 서버 호출
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.ml_server_url}/ocr/extract",
                    json={
                        "public_image_path": context.public_file_path,
                        "private_image_path": context.input_file_path,
                    },
                )
                response.raise_for_status()

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            # 네트워크 오류 → 재시도 가능
            raise RetryableError("OCRStage", f"Network error: {str(e)}") from e

        except httpx.HTTPStatusError as e:
            # HTTP 오류
            if e.response.status_code >= 500:
                # 서버 오류 → 재시도 가능
                raise RetryableError("OCRStage", f"Server error: {str(e)}") from e
            else:
                # 클라이언트 오류 → 재시도 불가
                raise ValueError(f"OCR request failed: {str(e)}") from e

        # 결과 저장 (OCRResult 스키마 사용)
        ocr_data = response.json()

        context.ocr_result = OCRResult(
            text=ocr_data.get("text", ""),
            confidence=ocr_data.get("confidence", 0.0),
            bbox=ocr_data.get("text_boxes"),
            metadata=ocr_data.get("metadata", {}),
        )

        return context

    def validate_output(self, context: PipelineContext) -> None:
        """출력 검증: OCR 결과에 텍스트가 있는지 확인

        Args:
            context: 파이프라인 컨텍스트

        Raises:
            ValueError: OCR 결과가 없거나 텍스트가 없을 때
        """
        if not context.ocr_result:
            raise ValueError("OCR result is empty")

        # if not context.ocr_result.bbox:
        #     raise ValueError("OCR failed to extract text")

    def save_db(self, context: PipelineContext):
        ocr_result = context.ocr_result
        if ocr_result is None:
            return

        with get_db_manager().get_sync_session() as session:
            if not session:
                raise RuntimeError("DB 세션 생성 실패")

            # OCRExecution 생성
            ocr_execution_data = OCRExecutionCreate(
                chain_id=context.context_id,
                image_path=context.input_file_path,
                public_path=context.public_file_path,
                status="success",
                error="",
            )

            db_ocr_execution = ocr_execution_crud.create(
                db=session, obj_in=ocr_execution_data
            )

            ocr_execution = OCRResultDTO.model_validate(db_ocr_execution)

            for box in ocr_result.bbox:
                text_box_data = OCRTextBoxCreate(
                    ocr_execution_id=ocr_execution.id,
                    text=box.text,
                    confidence=box.confidence,
                    bbox=box.bbox,
                )

                ocr_text_box_crud.create(db=session, obj_in=text_box_data)
