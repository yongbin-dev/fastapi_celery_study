# app/utils/file_utils.py
"""파일 처리 유틸리티"""

import os
from pathlib import Path
from typing import Tuple

from fastapi import File
from supabase import Client, create_client

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Supabase 클라이언트 초기화
supabase: Client = create_client(
    settings.NEXT_PUBLIC_SUPABASE_URL,
    settings.NEXT_PUBLIC_SUPABASE_ANON_KEY,
)

BUCKET_NAME = "my-bucket"


def save_uploaded_image(file: File, filename: str) -> str:
    """
    업로드된 이미지를 저장하고 경로를 반환합니다.

    Args:
        image_data: 이미지 바이너리 데이터
        filename: 원본 파일명

    Returns:
        str: 저장된 파일의 상대 경로 (images/YYYYMMDD/uuid_filename.ext)
    """
    try:
        contents = await file.read()

        response = supabase.storage.from_(BUCKET_NAME).upload(
            path=f"uploads/{file.filename}",
            file=contents,
            file_options={"content-type": file.content_type},
        )

        logger.info(f"superbase : {response}")

        # Public URL 가져오기
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(
            f"uploads/{file.filename}"
        )

        return {"response": response, "public_url": public_url}
        # 기본 저장 디렉토리

        # base_dir = Path("images")

        # # 날짜별 서브디렉토리 생성 (YYYYMMDD)
        # date_str = datetime.now().strftime("%Y%m%d")
        # save_dir = base_dir / date_str
        # save_dir.mkdir(parents=True, exist_ok=True)

        # # 파일명 생성 (UUID + 원본 파일명)
        # file_ext = Path(filename).suffix
        # unique_filename = f"{uuid.uuid4()}{file_ext}"
        # file_path = save_dir / unique_filename

        # # 파일 저장
        # with open(file_path, "wb") as f:
        #     f.write(image_data)

        # # 상대 경로 반환
        # relative_path = str(file_path)
        # logger.info(f"이미지 저장 완료: {relative_path}")

    except Exception as e:
        logger.error(f"이미지 저장 실패: {str(e)}")
        raise


def get_file_size_mb(file_path: str) -> float:
    """파일 크기를 MB 단위로 반환"""
    return os.path.getsize(file_path) / (1024 * 1024)


def validate_image_file(filename: str) -> Tuple[bool, str]:
    """
    이미지 파일 유효성 검사

    Args:
        filename: 파일명

    Returns:
        Tuple[bool, str]: (유효 여부, 에러 메시지)
    """
    allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

    file_ext = Path(filename).suffix.lower()

    if file_ext not in allowed_extensions:
        allowed = ", ".join(allowed_extensions)
        return False, f"지원하지 않는 파일 형식입니다. 허용: {allowed}"

    return True, ""
