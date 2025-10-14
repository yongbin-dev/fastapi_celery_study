# app/domains/common/services/common_service.py
"""공통 서비스 - 파일 저장 및 DB 저장 로직"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domains.ocr.schemas import OCRResultDTO
from app.domains.ocr.schemas.ocr_db import OCRExecutionCreate, OCRTextBoxCreate
from app.domains.ocr.schemas.response import OCRExtractResponse
from app.repository.crud.async_crud import ocr_execution_crud, ocr_text_box_crud
from app.schemas.common import ImageResponse
from app.shared.base_service import BaseService
from app.utils.file_utils import save_uploaded_image

logger = get_logger(__name__)


class CommonService(BaseService):
    """공통 서비스 클래스"""

    def load_image(self):
        pass
        # create AsyncSession and sign in
        # retrieve the current user's session for authentication

        #     f"{settings.NEXT_PUBLIC_SUPABASE_URL}/storage/v1/upload/resumable",
        #     headers={"Authorization": f"Bearer {access_token}", "x-upsert": "true"},
        # )
        # uploader = my_AsyncSession.uploader(
        #     file_stream=file,
        #     chunk_size=(6 * 1024 * 1024),
        #     metadata={
        #         "bucketName": bucket_name,
        #         "objectName": file_name,
        #         "contentType": "image/png",
        #         "cacheControl": "3600",
        #     },
        # )
        # uploader.upload()

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

    async def get_ocr_list(self, db: AsyncSession) -> list[OCRExtractResponse]:
        ocr_executions = await ocr_execution_crud.get_all(db)
        return [OCRExtractResponse.model_validate(oer) for oer in ocr_executions]

    async def get_image_by_id(self, db: AsyncSession, id: int) -> OCRExtractResponse:
        ocr_execution = await ocr_execution_crud.get(db, id)
        return OCRExtractResponse.model_validate(ocr_execution)

    async def save_ocr_execution_to_db(
        self,
        db: AsyncSession,
        image_response: ImageResponse,
        ocr_result: OCRResultDTO,
        chain_id: Optional[str] = None,
    ) -> OCRResultDTO:
        """
        OCR 실행 정보를 데이터베이스에 저장합니다.

        Args:
            image_path: 저장된 이미지 경로
            ocr_result: OCR 처리 결과
            chain_id: Celery chain ID (선택적)

        Returns:
            OCRExecution: 저장된 OCR 실행 정보 객체
        """
        logger.info("OCR 실행 정보 DB 저장 시작")

        # OCRExecution 생성
        ocr_execution_data = OCRExecutionCreate(
            chain_id=chain_id,
            image_path=image_response.private_img,
            public_path=image_response.public_img,
            status=ocr_result.status,
            error=ocr_result.error,
        )
        db_ocr_execution = await ocr_execution_crud.create(
            db=db, obj_in=ocr_execution_data
        )

        # OCRTextBox 생성
        for box in ocr_result.text_boxes:
            text_box_data = OCRTextBoxCreate(
                ocr_execution_id=db_ocr_execution.id,  # type: ignore
                text=box.text,
                confidence=box.confidence,
                bbox=box.bbox,
            )

            await ocr_text_box_crud.create(db=db, obj_in=text_box_data)

        logger.info(f"OCR 실행 정보 DB 저장 완료: ID={db_ocr_execution.id}")
        return OCRResultDTO.model_validate(db_ocr_execution)


# 싱글톤 인스턴스
common_service = CommonService()


def get_common_service() -> CommonService:
    return common_service
