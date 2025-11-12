"""BentoML OCR 서비스

BentoML을 사용한 OCR 모델 서빙
기존 gRPC 서비스와 병행하여 HTTP API 제공
"""

from typing import List

import bentoml
from ml_app.models.ocr_model import get_ocr_model
from pydantic import BaseModel, Field
from shared.core.logging import get_logger
from shared.schemas.ocr_db import OCRExtractDTO
from shared.service.common_service import get_common_service

logger = get_logger(__name__)


# === Request/Response 스키마 ===
class OCRRequest(BaseModel):
    """OCR 요청 스키마"""

    private_img: str = Field(default="", description="이미지 path")
    language: str = Field(
        default="korean", description="OCR 언어 (korean, english, chinese 등)"
    )
    confidence_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="신뢰도 임계값"
    )
    use_angle_cls: bool = Field(default=True, description="텍스트 각도 분류 사용 여부")


class BatchOCRRequest(BaseModel):
    """배치 OCR 요청 스키마"""

    language: str = Field(default="korean", description="OCR 언어")
    confidence_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="신뢰도 임계값"
    )
    use_angle_cls: bool = Field(default=True, description="텍스트 각도 분류 사용 여부")


class BatchOCRResponse(BaseModel):
    """배치 OCR 응답 스키마"""

    results: List[OCRExtractDTO] = Field(description="OCR 결과 리스트")
    total_processed: int = Field(description="처리된 이미지 수")
    total_success: int = Field(description="성공한 이미지 수")
    total_failed: int = Field(description="실패한 이미지 수")


class HealthCheckResponse(BaseModel):
    """헬스 체크 응답 스키마"""

    status: str = Field(description="서비스 상태 (healthy/unhealthy)")
    engine_type: str = Field(description="OCR 엔진 타입")
    model_loaded: bool = Field(description="모델 로드 여부")
    version: str = Field(description="서비스 버전")
    error: str | None = Field(default=None, description="에러 메시지")


# === BentoML 서비스 정의 ===
@bentoml.service(
    name="ocr_service",
    resources={
        "cpu": "2",
        "memory": "4Gi",
    },
)
class OCRBentoService:
    """BentoML OCR 서비스

    OCR 모델을 BentoML로 서빙하는 서비스
    기존 Factory 패턴의 OCR 엔진을 활용
    """

    def __init__(self):
        """서비스 초기화"""
        from shared.config import settings

        self.engine_type = settings.OCR_ENGINE
        logger.info(f"OCRBentoService 초기화: engine={self.engine_type}")

    @bentoml.api
    async def extract_text(
        self,
        request_data: OCRRequest,
    ) -> OCRExtractDTO:
        """단일 이미지에서 텍스트 추출

        Args:
            image: PIL 이미지 객체
            request_data: OCR 요청 파라미터

        Returns:
            OCR 결과
        """
        try:
            private_img = request_data.private_img
            logger.info(f"private_img : {private_img}")
            image_data = await get_common_service().load_image(private_img)
            logger.info(
                f"OCR 요청: lang={request_data.language}, size={len(image_data)}"
            )
            # PIL 이미지를 바이트로 변환

            # OCR 모델 실행
            model = get_ocr_model(
                use_angle_cls=request_data.use_angle_cls, lang=request_data.language
            )
            result = model.predict(
                image_data, confidence_threshold=request_data.confidence_threshold
            )

            return result

        except Exception as e:
            logger.error(f"OCR 실패: {str(e)}", exc_info=True)
            raise

    @bentoml.api
    async def extract_text_batch(
        self,
        request_data: BatchOCRRequest,
        private_imgs: List[str],
    ) -> BatchOCRResponse:
        """배치 이미지에서 텍스트 추출

        Args:
            private_imgs: 이미지 경로 리스트
            request_data: OCR 요청 파라미터

        Returns:
            배치 OCR 결과
        """
        results = []
        success_count = 0
        failed_count = 0

        logger.info(
            f"배치 OCR 요청: 이미지 수={len(private_imgs)},lang={request_data.language}"
        )

        # 각 이미지를 순차적으로 처리
        for idx, private_img in enumerate(private_imgs):
            try:
                # 이미지 로드
                image_data = await get_common_service().load_image(private_img)

                # OCR 모델 실행
                model = get_ocr_model(
                    use_angle_cls=request_data.use_angle_cls,
                    lang=request_data.language,
                )
                result = model.predict(
                    image_data,
                    confidence_threshold=request_data.confidence_threshold,
                )

                results.append(result)
                success_count += 1
                logger.info(f"이미지 {idx + 1}/{len(private_imgs)} 처리 성공")

            except Exception as e:
                failed_count += 1
                logger.error(
                    f"이미지 {idx + 1}/{len(private_imgs)} 처리 실패: {str(e)}",
                    exc_info=True,
                )
                # 실패한 경우 빈 결과 추가
                results.append(
                    OCRExtractDTO(
                        text_boxes=[],
                        status="",
                        error="true",
                    )
                )

        logger.info(
            f"배치 OCR 완료: 총 {len(private_imgs)}개, "
            f"성공 {success_count}개, 실패 {failed_count}개"
        )

        return BatchOCRResponse(
            results=results,
            total_processed=len(private_imgs),
            total_success=success_count,
            total_failed=failed_count,
        )

    @bentoml.api
    async def health_check(self) -> HealthCheckResponse:
        """헬스 체크

        Returns:
            헬스 체크 결과
        """
        try:
            model = get_ocr_model()

            return HealthCheckResponse(
                status="healthy" if model.is_loaded else "unhealthy",
                engine_type=self.engine_type,
                model_loaded=model.is_loaded,
                version="1.0.0",
            )

        except Exception as e:
            logger.error(f"헬스 체크 실패: {str(e)}", exc_info=True)
            return HealthCheckResponse(
                status="unhealthy",
                engine_type="unknown",
                model_loaded=False,
                version="1.0.0",
                error=str(e),
            )
