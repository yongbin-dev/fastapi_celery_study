"""OCR 처리 스테이지

ML 서버를 호출하여 이미지/PDF 파일에서 텍스트를 추출합니다.
"""

import grpc
import httpx
from app.domains.ocr.schemas.response import OCRResultDTO
from celery.beat import get_logger
from shared.config import settings
from shared.core.database import get_db_manager
from shared.grpc.generated import common_pb2
from shared.pipeline.context import OCRResult, PipelineContext
from shared.pipeline.exceptions import RetryableError
from shared.pipeline.stage import PipelineStage
from shared.repository.crud.sync_crud import ocr_execution_crud, ocr_text_box_crud
from shared.schemas import OCRExecutionCreate
from shared.schemas.ocr_db import OCRTextBoxCreate

logger = get_logger(__name__)

# Feature Flag
USE_GRPC = settings.USE_GRPC == "true"


class OCRStage(PipelineStage):
    """OCR 처리 스테이지 (HTTP/gRPC 듀얼 모드)

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
        """ML 서버에 OCR 요청 (HTTP 또는 gRPC)

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            업데이트된 컨텍스트 (ocr_result 포함)

        Raises:
            RetryableError: 네트워크 오류 또는 서버 오류
            ValueError: 클라이언트 오류
        """

        if USE_GRPC:
            logger.info("gRPC 모드로 OCR 실행")
            return await self._execute_grpc(context)
        else:
            logger.info("HTTP 모드로 OCR 실행")
            return await self._execute_http(context)

    async def _execute_http(self, context: PipelineContext) -> PipelineContext:
        """HTTP로 OCR 실행 (기존 방식)"""
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
            raise RetryableError("OCRStage", f"HTTP error: {str(e)}") from e

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

        logger.info("HTTP OCR 완료")
        return context

    async def _execute_grpc(self, context: PipelineContext) -> PipelineContext:
        """gRPC로 OCR 실행 (신규 방식)"""
        from tasks.grpc_clients.ocr_client import OCRGrpcClient

        try:
            # gRPC 클라이언트를 컨텍스트 매니저로 사용 (매 요청마다 새 연결 생성)
            async with OCRGrpcClient() as client:
                # gRPC 호출
                response = await client.extract_text(
                    public_image_path=context.public_file_path,
                    private_image_path=context.input_file_path,
                    language="korean",
                    confidence_threshold=0.5,
                    use_angle_cls=True,
                )

                # 성공 여부 확인
                if response.status != common_pb2.STATUS_SUCCESS:
                    error_msg = (
                        response.error.message if response.error else "Unknown error"
                    )
                    raise ValueError(f"gRPC OCR failed: {error_msg}")

                # Protobuf → OCRResult 변환
                text_boxes = []
                for box in response.text_boxes:
                    # bbox를 [[x1,y1], [x2,y2], ...] 형식으로 변환
                    coords = list(box.bbox.coordinates)
                    bbox_pairs = []
                    for i in range(0, len(coords), 2):
                        if i + 1 < len(coords):
                            bbox_pairs.append([coords[i], coords[i + 1]])

                    text_box_dict = {
                        "text": box.text,
                        "confidence": box.confidence,
                        "bbox": bbox_pairs,
                    }
                    text_boxes.append(text_box_dict)

                context.ocr_result = OCRResult(
                    text=response.text,
                    confidence=response.overall_confidence,
                    bbox=text_boxes,
                    metadata=dict(response.metadata.data),
                )

            logger.info("gRPC OCR 완료")
            return context

        except grpc.RpcError as e:
            # gRPC 오류 처리
            if e.code() in [
                grpc.StatusCode.UNAVAILABLE,
                grpc.StatusCode.DEADLINE_EXCEEDED,
            ]:
                # 재시도 가능한 오류
                raise RetryableError("OCRStage", f"gRPC error: {e.details()}") from e
            else:
                # 재시도 불가능한 오류
                raise ValueError(f"gRPC OCR failed: {e.details()}") from e

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
