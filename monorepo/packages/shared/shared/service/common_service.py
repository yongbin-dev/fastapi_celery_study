# app/domains/common/services/common_service.py
"""공통 서비스 - 파일 저장 및 DB 저장 로직"""

from typing import Optional

from app.domains.ocr.schemas import OCRResultDTO
from shared.core.logging import get_logger
from shared.repository.crud.async_crud import ocr_execution_crud, ocr_text_box_crud
from shared.schemas.common import ImageResponse
from shared.schemas.ocr_db import OCRExecutionCreate, OCRTextBoxCreate
from shared.service.base_service import BaseService
from shared.utils.file_utils import save_uploaded_image ,load_uploaded_image
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class CommonService(BaseService):
    """공통 서비스 클래스"""

    async def load_image(self , image_path : str) -> bytes :  
        return await load_uploaded_image(image_path);
      

    async def save_image(
        self, image_data: bytes, filename: str, content_type: str | None
    ) -> ImageResponse:
        """
        이미지 파일을 저장합니다.

        Args:
            image_data: 이미지 바이너리 데이터
            filename: 원본 파일명

        Returns:
            str: 저장된 파일의 상대 경로
        """
        logger.info(f"이미지 저장 시작: {filename}")
        image_response = await save_uploaded_image(image_data, filename, content_type)
        return image_response



# 싱글톤 인스턴스
common_service = CommonService()


def get_common_service() -> CommonService:
    return common_service
