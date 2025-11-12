"""OCR 처리 스테이지

ML 서버를 호출하여 이미지/PDF 파일에서 텍스트를 추출합니다.
"""

import grpc
from celery.beat import get_logger

# from models.ocr_model import get_ocr_model
from shared.config import settings
from shared.core.database import get_db_manager
from shared.grpc.generated import common_pb2
from shared.pipeline.context import PipelineContext
from shared.pipeline.exceptions import RetryableError
from shared.pipeline.stage import PipelineStage
from shared.repository.crud.sync_crud import ocr_execution_crud, ocr_text_box_crud
from shared.schemas import OCRExecutionCreate
from shared.schemas.enums import ProcessStatus
from shared.schemas.ocr_db import OCRExtractDTO, OCRTextBoxCreate
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
        self.common_service = get_common_service()
        self.MODEL_SERVER_URL = settings.MODEL_SERVER_URL

    def validate_input(self, context: PipelineContext) -> None:
        """입력 검증: 파일 경로가 있는지 확인

        Args:
            context: 파이프라인 컨텍스트

        Raises:
            ValueError: 입력 파일 경로가 없을 때
        """
        if context.is_batch:
            if not context.private_imgs or len(context.private_imgs) == 0:
                raise ValueError("private_imgs is required for batch processing")
        else:
            if not context.private_img:
                raise ValueError("private_img is required for single processing")

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """ML 서버에 OCR 요청 gRPC

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            업데이트된 컨텍스트 (ocr_result 포함)

        Raises:
            RetryableError: 네트워크 오류 또는 서버 오류
            ValueError: 클라이언트 오류
        """
        await self.execute_bento_ml(context)
        return context

    async def execute_bento_ml(self, context: PipelineContext) -> PipelineContext:
        """BentoML HTTP API로 OCR 요청 (단일/배치 지원)

        Args:
            context: 파이프라인 컨텍스트

        Returns:
            업데이트된 컨텍스트 (ocr_result 또는 ocr_results 포함)

        Raises:
            RetryableError: 네트워크 오류 또는 서버 오류
            ValueError: 클라이언트 오류
        """
        import httpx

        try:
            bentoml_url = f"{self.MODEL_SERVER_URL}"

            # 배치 처리 분기
            if context.is_batch and context.private_imgs:
                return await self._execute_batch(context, bentoml_url)
            else:
                return await self._execute_single(context, bentoml_url)

        except httpx.TimeoutException as e:
            raise RetryableError("OCRStage", f"BentoML timeout: {str(e)}") from e

        except httpx.ConnectError as e:
            error_msg = f"BentoML connection error: {str(e)}"
            raise RetryableError("OCRStage", error_msg) from e

        except Exception as e:
            logger.error(f"BentoML OCR 실패: {str(e)}", exc_info=True)
            raise ValueError(f"BentoML OCR failed: {str(e)}") from e

    async def _execute_single(
        self, context: PipelineContext, bentoml_url: str
    ) -> PipelineContext:
        """단일 이미지 OCR 처리

        Args:
            context: 파이프라인 컨텍스트
            bentoml_url: BentoML 서버 URL

        Returns:
            업데이트된 컨텍스트 (ocr_result 포함)
        """
        import json

        import httpx

        logger.info(f"단일 BentoML OCR 요청: {context.private_img}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            request_data = {
                "private_img": context.private_img,
                "language": context.options.get("language", "korean"),
                "confidence_threshold": context.options.get(
                    "confidence_threshold", 0.5
                ),
                "use_angle_cls": context.options.get("use_angle_cls", True),
            }
            data = {"request_data": json.dumps(request_data)}

            response = await client.post(
                f"{bentoml_url}/extract_text",
                data=data,
            )

            # 응답 확인
            if response.status_code != 200:
                error_msg = (
                    f"BentoML API failed: {response.status_code} - {response.text}"
                )
                if response.status_code >= 500:
                    raise RetryableError("OCRStage", error_msg)
                else:
                    raise ValueError(error_msg)

            # JSON 응답 파싱
            result = response.json()

            # OCRExtractDTO로 변환
            text_boxes = []
            for box in result.get("text_boxes", []):
                text_box_dict = {
                    "text": box["text"],
                    "confidence": box["confidence"],
                    "bbox": box["bbox"],
                }
                text_boxes.append(text_box_dict)

            context.ocr_result = OCRExtractDTO(
                text_boxes=text_boxes,
                status=ProcessStatus.STARTED,
            )

            logger.info(f"단일 BentoML OCR 완료: {len(text_boxes)} 텍스트 박스")
            return context

    async def _execute_batch(
        self, context: PipelineContext, bentoml_url: str
    ) -> PipelineContext:
        """배치 이미지 OCR 처리

        Args:
            context: 파이프라인 컨텍스트
            bentoml_url: BentoML 서버 URL

        Returns:
            업데이트된 컨텍스트 (ocr_results 포함)
        """
        import httpx

        if context.private_imgs is None:
            return context

        logger.info(f"배치 BentoML OCR 요청: {len(context.private_imgs)}개 이미지")

        # 배치는 타임아웃을 길게 설정 (이미지 개수 * 10초 + 기본 30초)
        timeout = 30.0 + (len(context.private_imgs) * 10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            payload = {
                "request_data": {
                    "language": context.options.get("language", "korean"),
                    "confidence_threshold": context.options.get(
                        "confidence_threshold", 0.5
                    ),
                    "use_angle_cls": context.options.get("use_angle_cls", True),
                },
                "private_imgs": context.private_imgs,
            }

            response = await client.post(
                f"{bentoml_url}/extract_text_batch",
                json=payload,
            )

            # 응답 확인
            if response.status_code != 200:
                error_msg = (
                    f"BentoML Batch API failed: "
                    f"{response.status_code} - {response.text}"
                )

                if response.status_code >= 500:
                    raise RetryableError("OCRStage", error_msg)
                else:
                    raise ValueError(error_msg)

            # BatchOCRResponse 파싱
            result = response.json()

            # OCRExtractDTO 리스트로 변환
            ocr_results = []
            for r in result["results"]:
                text_boxes = []
                for box in r.get("text_boxes", []):
                    text_box_dict = {
                        "text": box["text"],
                        "confidence": box["confidence"],
                        "bbox": box["bbox"],
                    }
                    text_boxes.append(text_box_dict)

                # 텍스트 박스가 있으면 성공, 없으면 실패로 간주
                status = ProcessStatus.STARTED if text_boxes else ProcessStatus.FAILURE

                ocr_results.append(
                    OCRExtractDTO(
                        text_boxes=text_boxes,
                        status=status,
                    )
                )

            context.ocr_results = ocr_results

            logger.info(
                f"배치 BentoML OCR 완료: {result['total_success']}/"
                f"{result['total_processed']} 성공"
            )
            return context

    async def execute_grpc(self, context: PipelineContext) -> PipelineContext:
        """gRPC로 OCR 실행 (신규 방식)"""
        from tasks.grpc_clients.ocr_client import OCRGrpcClient

        try:
            # gRPC 클라이언트를 컨텍스트 매니저로 사용 (매 요청마다 새 연결 생성)
            async with OCRGrpcClient() as client:
                # gRPC 호출
                response = await client.extract_text(
                    public_image_path=context.public_file_path,
                    private_image_path=context.private_img,
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

                context.ocr_result = OCRExtractDTO(
                    text_boxes=text_boxes,
                    status=ProcessStatus.STARTED,
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
        if context.is_batch:
            if not context.ocr_results or len(context.ocr_results) == 0:
                raise ValueError("OCR batch results are empty")
        else:
            if not context.ocr_result:
                raise ValueError("OCR result is empty")

    def save_db(self, context: PipelineContext):
        """OCR 결과를 DB에 저장 (단일/배치 지원)

        Args:
            context: 파이프라인 컨텍스트
        """
        if context.is_batch:
            self._save_batch_db(context)
        else:
            self._save_single_db(context)

    def _save_single_db(self, context: PipelineContext):
        """단일 OCR 결과를 DB에 저장

        Args:
            context: 파이프라인 컨텍스트
        """
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

            # 텍스트 박스 저장
            for box in ocr_result.text_boxes:
                text_box_data = OCRTextBoxCreate(
                    ocr_execution_id=db_ocr_execution.id,
                    text=box.text,
                    confidence=box.confidence,
                    bbox=box.bbox,
                )

                ocr_text_box_crud.create(db=session, obj_in=text_box_data)

            logger.info(
                f"단일 OCR 결과 DB 저장 완료: execution_id={db_ocr_execution.id}"
            )

    def _save_batch_db(self, context: PipelineContext):
        """배치 OCR 결과를 DB에 저장

        각 이미지마다 개별 chain_id를 생성하여 저장합니다.

        Args:
            context: 파이프라인 컨텍스트
        """
        import uuid

        from shared.repository.crud.sync_crud.chain_execution import (
            chain_execution_crud,
        )

        ocr_results = context.ocr_results
        if not ocr_results or len(ocr_results) == 0:
            return

        with get_db_manager().get_sync_session() as session:
            if not session:
                raise RuntimeError("DB 세션 생성 실패")

            # 각 이미지의 OCR 결과를 개별적으로 저장
            for idx, ocr_result in enumerate(ocr_results):
                # private_imgs와 public_file_paths가 있는지 확인
                if context.private_imgs is None:
                    break

                image_path = (
                    context.private_imgs[idx] if idx < len(context.private_imgs) else ""
                )
                public_path = (
                    context.public_file_paths[idx]
                    if context.public_file_paths
                    and idx < len(context.public_file_paths)
                    else ""
                )

                # 각 이미지마다 개별 chain_id 생성
                individual_chain_id = str(uuid.uuid4())

                # ChainExecution 생성 (각 이미지마다)
                chain_execution_crud.create_chain_execution(
                    db=session,
                    chain_id=individual_chain_id,
                    batch_id=context.batch_id if context.batch_id else None,
                    chain_name=f"batch_image_{idx}",
                    total_tasks=1,
                    initiated_by="batch_ocr",
                    input_data={"image_path": image_path, "index": idx},
                )

                # OCRExecution 생성
                status = "success" if ocr_result.text_boxes else "failed"
                error = "" if ocr_result.text_boxes else "No text boxes extracted"

                ocr_execution_data = OCRExecutionCreate(
                    chain_id=individual_chain_id,  # 개별 chain_id 사용
                    image_path=image_path,
                    public_path=public_path,
                    status=status,
                    error=error,
                )

                db_ocr_execution = ocr_execution_crud.create(
                    db=session, obj_in=ocr_execution_data
                )

                # 텍스트 박스 저장 (있는 경우에만)
                for box in ocr_result.text_boxes:
                    text_box_data = OCRTextBoxCreate(
                        ocr_execution_id=db_ocr_execution.id,
                        text=box.text,
                        confidence=box.confidence,
                        bbox=box.bbox,
                    )

                    ocr_text_box_crud.create(db=session, obj_in=text_box_data)

            logger.info(
                f"배치 OCR 결과 DB 저장 완료: {len(ocr_results)}개 execution 생성"
            )
