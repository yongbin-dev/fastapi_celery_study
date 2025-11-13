"""Storage 경로 생성 유틸리티

파일 저장 경로를 일관되게 생성하기 위한 유틸리티 클래스
"""

import uuid
from datetime import datetime


class StoragePathBuilder:
    """Storage 경로 생성기"""

    @staticmethod
    def build_pdf_path(filename: str) -> tuple[str, str]:
        """PDF 저장 경로 및 폴더명 생성

        uploads/{YYYYMMDD}/{UUID}/{filename}.pdf 형식으로 경로 생성

        Args:
            filename: 원본 파일명

        Returns:
            tuple[str, str]: (전체 경로, 폴더명)

        Example:
            >>> path, folder = StoragePathBuilder.build_pdf_path("document.pdf")
            >>> path
            'uploads/20251113/a3b02055-1f4b-4520-8b69-65036c3ecebe/document.pdf'
            >>> folder
            'uploads/20251113/a3b02055-1f4b-4520-8b69-65036c3ecebe'
        """
        now = datetime.now()
        date_folder = now.strftime("%Y%m%d")
        uuid_folder = str(uuid.uuid4())
        folder = f"uploads/{date_folder}/{uuid_folder}"

        # 확장자를 안전하게 제거
        base_filename = filename.rsplit(".", 1)[0] if "." in filename else filename

        path = f"{folder}/{base_filename}.pdf"
        return path, folder

    @staticmethod
    def build_image_path(
        folder: str, filename: str, page_num: int | None = None
    ) -> str:
        """이미지 저장 경로 생성

        기존 폴더 구조를 유지하면서 이미지 경로 생성
        페이지 번호가 있으면 page_{num}.png 형식 사용

        Args:
            folder: 기존 폴더 경로 (예: 'uploads/20251113/uuid')
            filename: 원본 파일명
            page_num: 페이지 번호 (선택)

        Returns:
            str: 이미지 경로

        Example:
            >>> StoragePathBuilder.build_image_path("uploads/20251113/uuid", "doc", 1)
            'uploads/20251113/uuid/page_1.png'
        """
        if page_num is not None:
            image_filename = f"page_{page_num}.png"
        else:
            base_filename = filename.rsplit(".", 1)[0] if "." in filename else filename
            image_filename = f"{base_filename}.png"

        return f"{folder}/{image_filename}"

    @staticmethod
    def build_generic_path(filename: str, subfolder: str = "uploads") -> str:
        """범용 파일 경로 생성

        uploads/{YYYYMMDD}/{filename} 형식으로 경로 생성
        (레거시 save_uploaded_file 호환)

        Args:
            filename: 파일명 (경로 포함 가능)
            subfolder: 최상위 폴더 (기본: 'uploads')

        Returns:
            str: 파일 경로

        Example:
            >>> StoragePathBuilder.build_generic_path("test.jpg")
            'uploads/20251113/test.jpg'
        """
        now = datetime.now()
        date_folder = now.strftime("%Y%m%d")
        return f"{subfolder}/{date_folder}/{filename}"

    @staticmethod
    def extract_folder_from_path(file_path: str) -> str:
        """파일 경로에서 폴더 경로 추출

        PDF 파일 경로에서 폴더 부분만 추출하여 페이지 이미지 저장 시 사용

        Args:
            file_path: 파일 전체 경로

        Returns:
            str: 폴더 경로

        Example:
            >>> path = "uploads/20251113/uuid/document.pdf"
            >>> StoragePathBuilder.extract_folder_from_path(path)
            'uploads/20251113/uuid'
        """
        # URL이나 경로에서 폴더 부분만 추출
        path_parts = file_path.split("/")

        # 'uploads' 다음의 두 부분이 폴더 (날짜/UUID)
        if "uploads" in path_parts:
            uploads_index = path_parts.index("uploads")
            if len(path_parts) > uploads_index + 2:
                # uploads/{date}/{uuid} 형식
                return "/".join(path_parts[: uploads_index + 3])

        # Fallback: 마지막 파일명만 제거
        return "/".join(path_parts[:-1]) if len(path_parts) > 1 else ""
