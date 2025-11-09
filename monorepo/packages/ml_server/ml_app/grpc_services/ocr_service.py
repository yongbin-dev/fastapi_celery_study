# packages/ml_server/ml_app/grpc_services/ocr_service.py
"""OCR gRPC 서비스 구현"""

import grpc
from ml_app.models.ocr_model import get_ocr_model
from shared.core.logging import get_logger
from shared.grpc.generated import common_pb2, ocr_pb2, ocr_pb2_grpc  # type: ignore
from shared.service.common_service import CommonService

logger = get_logger(__name__)


class OCRServiceServicer(ocr_pb2_grpc.OCRServiceServicer):
    """OCR gRPC 서비스"""

    def __init__(self):
        self.common_service = CommonService()
        logger.info("OCR gRPC 서비스 초기화 완료")

    async def extract_text(
        self, request: ocr_pb2.OCRRequest, context: grpc.aio.ServicerContext
    ) -> ocr_pb2.OCRResponse:
        """단일 이미지 OCR 추출

        Args:
            request: OCR 요청
            context: gRPC 컨텍스트

        Returns:
            OCR 응답
        """
        try:
            logger.info(f"gRPC OCR 요청: {request.private_image_path}")

            # 1. 이미지 로드
            image_data = await self.common_service.load_image(
                request.private_image_path
            )

            # 2. OCR 모델 실행 (요청에 값이 없으면 settings 기본값 사용)
            from shared.config import settings

            # 요청 파라미터 또는 기본값 사용
            use_angle_cls = settings.OCR_USE_ANGLE_CLS
            lang = request.language if request.language else settings.OCR_LANG

            model = get_ocr_model(use_angle_cls=use_angle_cls, lang=lang)

            result = model.predict(
                image_data,
                confidence_threshold=request.confidence_threshold
                if request.confidence_threshold
                else 0.5,
            )

            # 3. Protobuf 응답 생성
            response = ocr_pb2.OCRResponse(
                status=common_pb2.STATUS_SUCCESS,
                text="",  # 전체 텍스트는 text_boxes에서 추출
                overall_confidence=0.0,
            )

            # 4. 텍스트 박스 변환
            total_confidence = 0.0
            all_text = []

            for box in result.text_boxes:
                # bbox를 flat list로 변환
                bbox_coords = []
                if hasattr(box, "bbox") and box.bbox:
                    if isinstance(box.bbox, list):
                        # 중첩 리스트인 경우 flatten
                        for coord in box.bbox:
                            if isinstance(coord, list):
                                bbox_coords.extend(coord)
                            else:
                                bbox_coords.append(float(coord))
                    else:
                        bbox_coords = [float(box.bbox)]

                text_box = ocr_pb2.TextBox(
                    text=box.text,
                    confidence=box.confidence,
                    bbox=common_pb2.BoundingBox(coordinates=bbox_coords),
                )
                response.text_boxes.append(text_box)

                all_text.append(box.text)
                total_confidence += box.confidence

            # 전체 텍스트 및 평균 신뢰도 계산
            response.text = " ".join(all_text)
            if len(result.text_boxes) > 0:
                response.overall_confidence = total_confidence / len(result.text_boxes)

            # 5. 메타데이터 (OCRExtractDTO에는 metadata가 없으므로 status만 저장)
            response.metadata.data["status"] = result.status

            logger.info(f"gRPC OCR 완료: {len(response.text_boxes)} 텍스트 박스")
            return response

        except Exception as e:
            logger.error(f"gRPC OCR 실패: {str(e)}", exc_info=True)

            # 에러 응답
            return ocr_pb2.OCRResponse(
                status=common_pb2.STATUS_FAILURE,
                text="",
                overall_confidence=0.0,
                error=common_pb2.ErrorInfo(
                    code="OCR_ERROR", message=str(e), details=type(e).__name__
                ),
            )

    async def extract_text_batch(
        self, request: ocr_pb2.OCRBatchRequest, context: grpc.aio.ServicerContext
    ):
        """배치 이미지 OCR 추출 (Server Streaming)

        Args:
            request: 배치 요청
            context: gRPC 컨텍스트

        Yields:
            진행 상황 스트림
        """
        import uuid

        batch_id = str(uuid.uuid4())
        total = len(request.image_paths)

        logger.info(f"gRPC 배치 OCR 시작: {batch_id}, {total}개 이미지")

        result_img = []
        for idx, image_response in enumerate(request.image_paths):
            image_data = await self.common_service.load_image(
                image_path=image_response.private_path
            )

            result_img.append(image_data)

        model = get_ocr_model()
        result = model.predict_batch(
            result_img,
            confidence_threshold=request.confidence_threshold
            if request.confidence_threshold
            else 0.5,
        )

        logger.info(result)

    # request.image_paths
    # for idx, image_path in enumerate(request.image_paths):
    #     # 개별 OCR 요청 생성
    #     ocr_request = ocr_pb2.OCRRequest(
    #         public_image_path=image_path.public_path,
    #         private_image_path=image_path.private_path,
    #         language=request.language,
    #         confidence_threshold=request.confidence_threshold,
    #         use_angle_cls=request.use_angle_cls
    #     )

    #     # OCR 실행
    #     result = await self.ExtractText(ocr_request, context)

    #     # 진행 상황 전송
    #     progress = ocr_pb2.OCRBatchProgress(
    #         batch_id=batch_id,
    #         total_images=total,
    #         processed_images=idx + 1,
    #         current_result=result,
    #         progress_percentage=(idx + 1) / total * 100
    #     )

    #     yield progress

    # logger.info(f"gRPC 배치 OCR 완료: {batch_id}")

    async def check_health(
        self, request: ocr_pb2.HealthCheckRequest, context: grpc.aio.ServicerContext
    ) -> ocr_pb2.HealthCheckResponse:
        """헬스 체크

        Args:
            request: 헬스 체크 요청
            context: gRPC 컨텍스트

        Returns:
            헬스 체크 응답
        """
        from shared.config import settings

        try:
            model = get_ocr_model()

            return ocr_pb2.HealthCheckResponse(
                status=common_pb2.STATUS_SUCCESS
                if model.is_loaded
                else common_pb2.STATUS_FAILURE,
                engine_type=settings.OCR_ENGINE,
                model_loaded=model.is_loaded,
                version="1.0.0",
            )
        except Exception as e:
            logger.error(f"헬스 체크 실패: {str(e)}")
            return ocr_pb2.HealthCheckResponse(
                status=common_pb2.STATUS_FAILURE,
                engine_type="unknown",
                model_loaded=False,
                version="1.0.0",
            )
