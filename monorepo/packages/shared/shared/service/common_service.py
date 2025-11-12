# app/domains/common/services/common_service.py
"""공통 서비스 - 파일 저장 및 DB 저장 로직"""

import uuid
from typing import List

import fitz

from shared.core.logging import get_logger
from shared.schemas.common import ImageResponse
from shared.service.base_service import BaseService
from shared.utils.file_utils import (
    load_uploaded_image,
    save_uploaded_file,
    save_uploaded_image,
)

logger = get_logger(__name__)


class CommonService(BaseService):
    """공통 서비스 클래스"""

    async def save_pdf(
        self,
        original_filename: str,
        pdf_file_bytes: bytes,
    ) -> ImageResponse:
        """
        PDF 파일 원본만 저장하고 저장 경로를 반환합니다.

        저장 구조:
            {uuid}/{파일명}.pdf

        Args:
            pdf_file_bytes (bytes): PDF 파일의 바이트 데이터
            original_filename (str): 원본 PDF 파일명

        Returns:
            ImageResponse: 저장된 PDF 파일 정보
        """
        # 확장자를 안전하게 제거
        if "." in original_filename:
            base_filename = original_filename.rsplit(".", 1)[0]
        else:
            base_filename = original_filename

        # UUID 기반 폴더명 생성
        folder_name = f"{uuid.uuid4()}"

        # PDF 파일 저장
        pdf_filename = f"{folder_name}/{base_filename}.pdf"
        pdf_response = await self.save_file(
            image_data=pdf_file_bytes,
            filename=pdf_filename,
            content_type="application/pdf",
        )
        logger.info(f"✅ PDF 파일 저장 완료: {pdf_filename}")

        return pdf_response

    async def save_file(
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
        image_response = await save_uploaded_file(image_data, filename, content_type)
        return image_response

    async def download_and_split_pdf(
        self, pdf_url: str, original_filename: str
    ) -> List[ImageResponse]:
        """PDF를 다운로드하여 페이지별로 이미지로 변환하고 저장합니다.

        Args:
            pdf_url: 다운로드할 PDF의 URL
            original_filename: 원본 파일명
            common_service: 파일 저장을 위한 CommonService 인스턴스

        Returns:
            List[ImageResponse]: 변환된 이미지 정보 목록
        """
        logger.info(f"PDF 다운로드 시작: {pdf_url}")
        image_responses = []
        pdf_file_bytes = await self.load_image(pdf_url)

        # pdf_url에서 폴더 이름 추출
        # 예: 'yb_test_storage/uploads/20251112/a3b02055-1f4b-4520-8b69-65036c3ecebe/sd
        # -> '20251112/a3b02055-1f4b-4520-8b69-65036c3ecebe'
        path_parts = pdf_url.split("/")
        # 'uploads' 다음의 두 부분이 폴더 이름이 됩니다.
        if "uploads" in path_parts:
            uploads_index = path_parts.index("uploads")
            if len(path_parts) > uploads_index + 2:
                folder_name = (
                    f"{path_parts[uploads_index + 1]}/{path_parts[uploads_index + 2]}"
                )
            else:
                folder_name = str(
                    uuid.uuid4()
                )  # Fallback if path structure is unexpected
        else:
            folder_name = str(uuid.uuid4())  # Fallback if 'uploads' not in path

        with fitz.open(stream=pdf_file_bytes, filetype="pdf") as doc:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # 페이지를 이미지로 렌더링 (PNG)
                # 해상도 조절 (기본값 72dpi)
                # mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap()

                img_bytes = pix.tobytes("png")

                # 이미지 파일명 생성 (같은 폴더에 저장)
                image_filename = f"{folder_name}/page_{page_num + 1}.png"

                image_response = await save_uploaded_image(
                    image_data=img_bytes,
                    filename=image_filename,
                    content_type="image/png",
                )

                image_responses.append(image_response)
                logger.info(
                    f"'{original_filename}'의 {page_num + 1}"
                    f"번째 페이지를 이미지로 저장했습니다: {image_filename}"
                )

        return image_responses

    async def load_image(self, image_path: str) -> bytes:
        return await load_uploaded_image(image_path)


# 싱글톤 인스턴스
common_service = CommonService()


def get_common_service() -> CommonService:
    return common_service
