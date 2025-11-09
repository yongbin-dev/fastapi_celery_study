# app/domains/ocr/services/ocr_service.py

import httpx
from shared.config import settings
from shared.core.logging import get_logger
from shared.repository.crud import async_ocr_execution_crud
from shared.schemas.common import ImageResponse
from shared.service.base_service import BaseService
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import OCRResultDTO

logger = get_logger(__name__)


class OCRService(BaseService):
    """OCR 비즈니스 로직 서비스"""

    def __init__(self):
        super().__init__()
        self.ml_server_url = settings.MODEL_SERVER_URL
        self.timeout = settings.MODEL_SERVER_TIMEOUT

    async def get_all_ocr_executions(self, db: AsyncSession):
        ocr_executions = await async_ocr_execution_crud.get_multi_with_text_box(db)
        return [OCRResultDTO.model_validate(ce) for ce in ocr_executions]

    async def call_ml_server_pdf(
        self,
        image_response_list: list[ImageResponse],
    ):
        """
        ML 서버의 OCR API 호출

        Args:
            image_path: Supabase Storage에 저장된 이미지 경로
            language: 추출할 언어
            confidence_threshold: 신뢰도 임계값
            use_angle_cls: 각도 분류 사용 여부

        Returns:
            OCR 추출 결과
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.ml_server_url}/ocr/extract-pdf"
                data = {
                    "image_response_list": [x.dict() for x in image_response_list],
                }

                response = await client.post(url, json=data)
                response.raise_for_status()

                result = response.json()
                return result

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            logger.error(
                f"{self.ml_server_url}  "
                f"ML 서버 OCR 호출 실패 (HTTP {e.response.status_code})\n"
                f"에러 상세: {error_detail}"
            )
            raise Exception(f"ML 서버 OCR 호출 실패: {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"ML 서버 연결 실패: {str(e)}")
            raise Exception(f"ML 서버 연결 실패: {str(e)}")
        except Exception as e:
            logger.error(f"ML 서버 OCR 호출 중 예외 발생: {str(e)}")
            raise

    async def call_ml_server_ocr(
        self,
        chain_id: str,
        private_image_path: str,
        public_image_path: str,
        language: str = "korean",
        confidence_threshold: float = 0.5,
        use_angle_cls: bool = True,
    ):
        """
        ML 서버의 OCR API 호출

        Args:
            image_path: Supabase Storage에 저장된 이미지 경로
            language: 추출할 언어
            confidence_threshold: 신뢰도 임계값
            use_angle_cls: 각도 분류 사용 여부

        Returns:
            OCR 추출 결과
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.ml_server_url}/ocr/extract-async"
                data = {
                    "chain_id": chain_id,
                    "public_image_path": public_image_path,
                    "private_image_path": private_image_path,
                    "language": language,
                    "confidence_threshold": confidence_threshold,
                    "use_angle_cls": use_angle_cls,
                }

                logger.info(
                    f"ML 서버 OCR 호출 시작: {url}, 이미지 경로: {private_image_path}"
                )

                response = await client.post(url, json=data)
                response.raise_for_status()

                result = response.json()
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"ML 서버 OCR 호출 실패 (HTTP {e.response.status_code})")
            raise Exception(f"ML 서버 OCR 호출 실패: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"ML 서버 연결 실패: {str(e)}")
            raise Exception(f"ML 서버 연결 실패: {str(e)}")
        except Exception as e:
            logger.error(f"ML 서버 OCR 호출 중 예외 발생: {str(e)}")
            raise


ocr_service = OCRService()


def get_ocr_service():
    return ocr_service
