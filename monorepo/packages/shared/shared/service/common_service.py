# app/domains/common/services/common_service.py
"""공통 서비스 - 파일 저장 및 DB 저장 로직"""

import asyncio
from typing import List

import fitz

from shared.core.logging import get_logger
from shared.schemas.common import ImageResponse
from shared.service.base_service import BaseService
from shared.utils.file_utils import get_default_storage
from shared.utils.path_builder import StoragePathBuilder

logger = get_logger(__name__)


class CommonService(BaseService):
    """공통 서비스 클래스"""

    async def download_and_split_pdf(
        self, pdf_url: str, original_filename: str
    ) -> List[ImageResponse]:
        """PDF를 다운로드하여 페이지별로 이미지로 변환하고 병렬로 저장합니다.

        Args:
            pdf_url: 다운로드할 PDF의 URL (경로)
            original_filename: 원본 파일명

        Returns:
            List[ImageResponse]: 변환된 이미지 정보 목록
        """
        logger.info(f"📥 PDF 다운로드 시작: {pdf_url}")
        storage = get_default_storage()

        # 1. PDF 다운로드
        pdf_file_bytes = await storage.download(pdf_url)
        logger.info(f"✅ PDF 다운로드 완료: {len(pdf_file_bytes)} bytes")

        # 2. PDF 경로에서 폴더 추출 (같은 폴더에 이미지 저장)
        folder = StoragePathBuilder.extract_folder_from_path(pdf_url)
        logger.info(f"📁 이미지 저장 폴더: {folder}")

        # 3. PDF 페이지별 이미지 변환 (동기 작업)
        page_data_list = []
        with fitz.open(stream=pdf_file_bytes, filetype="pdf") as doc:
            total_pages = len(doc)
            logger.info(f"📄 총 {total_pages}페이지 변환 시작")

            for page_num in range(total_pages):
                page = doc.load_page(page_num)

                # 페이지를 PNG 이미지로 렌더링
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")

                # 이미지 경로 생성 (PathBuilder 사용)
                image_path = StoragePathBuilder.build_image_path(
                    folder=folder, filename=original_filename, page_num=page_num + 1
                )

                page_data_list.append(
                    {
                        "img_bytes": img_bytes,
                        "image_path": image_path,
                        "page_num": page_num + 1,
                    }
                )

        # 4. 병렬 업로드
        logger.info(f"🚀 {total_pages}개 페이지 병렬 업로드 시작")

        async def upload_page(page_data):
            """단일 페이지 업로드"""
            image_response = await storage.upload(
                file_data=page_data["img_bytes"],
                path=page_data["image_path"],
                content_type="image/png",
            )
            logger.info(
                f"✅ '{original_filename}' {page_data['page_num']}/{total_pages} "
                f"페이지 저장 완료: {page_data['image_path']}"
            )
            return image_response

        # asyncio.gather로 병렬 업로드 실행
        image_responses = await asyncio.gather(
            *[upload_page(page_data) for page_data in page_data_list]
        )

        logger.info(f"🎉 PDF 변환 완료: 총 {total_pages}개 이미지 병렬 생성")
        return list(image_responses)


# 싱글톤 인스턴스
common_service = CommonService()


def get_common_service() -> CommonService:
    return common_service
