# app/domains/common/services/common_service.py
"""공통 서비스 - 파일 저장 및 DB 저장 로직"""

import uuid

import fitz

from shared.core.logging import get_logger
from shared.schemas.common import ImageResponse
from shared.service.base_service import BaseService
from shared.utils.file_utils import load_uploaded_image, save_uploaded_image

logger = get_logger(__name__)


class CommonService(BaseService):
    """공통 서비스 클래스"""
    async def save_pdf(
        self,
        original_filename: str,
        pdf_file_bytes: bytes,
        ) ->  list[ImageResponse]:
        """
        PDF의 각 페이지를 이미지로 변환하여 저장하고,
        저장된 이미지 경로 리스트를 반환합니다.

        Args:
            pdf_file_bytes (bytes): PDF 파일의 바이트 데이터
            original_filename (str): 원본 PDF 파일명

        Returns:
            list[ImageResponse]: 각 페이지에 대해 저장된 이미지 정보
        """
        image_responses = []
        # 확장자를 안전하게 제거
        if '.' in original_filename:
            base_filename = original_filename.rsplit('.', 1)[0]

        encoded_base_filename = str(uuid.uuid4()) + "_" + base_filename

        with fitz.open(stream=pdf_file_bytes, filetype="pdf") as doc:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # 페이지를 이미지로 렌더링 (PNG)
                # 해상도 조절 (기본값 72dpi)
                # mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap()

                img_bytes = pix.tobytes("png")

                # 이미지 파일명 생성 (e.g., original_filename_page_1.png)
                image_filename = f"{encoded_base_filename}/page_{page_num + 1}.png"

                # 이미지 저장
                image_response = await self.save_image(
                    image_data=img_bytes,
                    filename=image_filename,
                    content_type="image/png"
                )
                image_responses.append(image_response)
                logger.info(
                    f"'{original_filename}'의 {page_num + 1}"
                    f"번째 페이지를 이미지로 저장했습니다: {image_filename}"
                )

        return image_responses

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


# 싱글톤 인스턴스
common_service = CommonService()


def get_common_service() -> CommonService:
    return common_service
