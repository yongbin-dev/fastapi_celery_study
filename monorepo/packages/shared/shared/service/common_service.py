# app/domains/common/services/common_service.py
"""공통 서비스 - 파일 저장 및 DB 저장 로직"""

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.logging import get_logger
from shared.repository.crud import async_ocr_execution_crud, async_ocr_text_box_crud
from shared.schemas.common import ImageResponse
from shared.schemas.ocr_db import OCRExecutionCreate, OCRTextBoxCreate
from shared.service.base_service import BaseService
from shared.utils.file_utils import load_uploaded_image, save_uploaded_image

logger = get_logger(__name__)


class CommonService(BaseService):
    """공통 서비스 클래스"""

    async def load_image(self, image_path: str) -> bytes:
        return await load_uploaded_image(image_path)

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

    async def save_ocr_execution_to_db(
        self,
        db: AsyncSession,
        image_response: Dict[str, Any],
        ocr_result: Dict[str, Any],
    ):
        """
        OCR 실행 결과를 DB에 저장합니다.

        Args:
            db: 데이터베이스 세션
            image_response: 이미지 저장 응답 (private_img, public_img 포함)
            ocr_result: ML 서버로부터 받은 OCR 결과

        Returns:
            저장된 OCR 실행 정보
        """
        try:
            # ocr_result에서 data 추출
            ocr_data = ocr_result.get("data", {})

            # OCRExecution 생성
            ocr_execution_data = OCRExecutionCreate(
                chain_id=None,  # 동기 처리이므로 chain_id 없음
                image_path=image_response.get("private_img", ""),
                public_path=image_response.get("public_img", ""),
                status=ocr_data.get("status", "success"),
                error=ocr_data.get("error"),
            )

            db_ocr_execution = await async_ocr_execution_crud.create(
                db=db, obj_in=ocr_execution_data
            )

            logger.info(f"OCR 실행 정보 DB 저장 완료: ID={db_ocr_execution.id}")

            # OCRTextBox 생성
            text_boxes = ocr_data.get("text_boxes", [])
            for box in text_boxes:
                text_box_data = OCRTextBoxCreate(
                    ocr_execution_id=db_ocr_execution.id,  # type: ignore
                    text=box.get("text", ""),
                    confidence=box.get("confidence", 0.0),
                    bbox=box.get("bbox", []),
                )

                await async_ocr_text_box_crud.create(db=db, obj_in=text_box_data)

            logger.info(f"OCR 텍스트 박스 {len(text_boxes)}개 DB 저장 완료")

            return db_ocr_execution

        except Exception as e:
            logger.error(f"OCR 결과 DB 저장 중 오류 발생: {str(e)}")
            raise


# 싱글톤 인스턴스
common_service = CommonService()


def get_common_service() -> CommonService:
    return common_service
