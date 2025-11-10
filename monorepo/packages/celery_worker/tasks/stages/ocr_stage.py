"""OCR 처리 스테이지

ML 서버를 호출하여 이미지/PDF 파일에서 텍스트를 추출합니다.
"""

from celery.beat import get_logger
from engines.models.ocr_model import get_ocr_model
from shared.config import settings
from shared.core.database import get_db_manager
from shared.pipeline.context import PipelineContext
from shared.pipeline.stage import PipelineStage
from shared.repository.crud.sync_crud import ocr_execution_crud, ocr_text_box_crud
from shared.schemas import OCRExecutionCreate
from shared.schemas.ocr_db import OCRTextBoxCreate
from shared.service.common_service import get_common_service

logger = get_logger(__name__)

# Feature Flag
USE_GRPC = settings.USE_GRPC == "true"


class OCRStage(PipelineStage):
    """OCR 처리 스테이지 (HTTP/gRPC 듀얼 모드)

    ML 서버의 OCR 엔진을 사용하여 텍스트를 추출합니다.
    """

    def __init__(self):
        super().__init__()
        self.model = get_ocr_model()
        self.common_service = get_common_service()
        self.ml_server_url = settings.MODEL_SERVER_URL

    def validate_input(self, context: PipelineContext) -> None:
        """입력 검증: 파일 경로가 있는지 확인

        Args:
            context: 파이프라인 컨텍스트

        Raises:
            ValueError: 입력 파일 경로가 없을 때
        """
        if not context.private_img:
            raise ValueError("private_img is required")

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """ML 서버에 OCR 요청 (HTTP 또는 gRPC)

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            업데이트된 컨텍스트 (ocr_result 포함)

        Raises:
            RetryableError: 네트워크 오류 또는 서버 오류
            ValueError: 클라이언트 오류
        """

        if self.model is None:
            raise Exception()

        image_data = await self.common_service.load_image(
            image_path=context.private_img
        )

        result = self.model.predict(
            image_data,
            confidence_threshold=0.5,
        )

        context.ocr_result = result

        logger.info("HTTP OCR 완료")
        return context
        # if USE_GRPC:
        #     logger.info("gRPC 모드로 OCR 실행")
        #     return await self._execute_grpc(context)
        # else:
        #     logger.info("HTTP 모드로 OCR 실행")
        #     return await self._execute_http(context)

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
                chain_id=context.chain_id,
                image_path=context.private_img,
                public_path=context.public_file_path,
                status="success",
                error="",
            )

            db_ocr_execution = ocr_execution_crud.create(
                db=session, obj_in=ocr_execution_data
            )

            for box in ocr_result.text_boxes:
                text_box_data = OCRTextBoxCreate(
                    ocr_execution_id=db_ocr_execution.id,
                    text=box.text,
                    confidence=box.confidence,
                    bbox=box.bbox,
                )

                ocr_text_box_crud.create(db=session, obj_in=text_box_data)
