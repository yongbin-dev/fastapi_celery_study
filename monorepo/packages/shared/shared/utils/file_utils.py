# app/utils/file_utils.py
"""파일 처리 유틸리티"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from supabase import Client, create_client

from ..config import settings
from ..core.logging import get_logger
from ..schemas.common import ImageResponse

logger = get_logger(__name__)

# Supabase 클라이언트 초기화 (환경 변수가 설정된 경우에만)
supabase: Optional[Client] = None
if settings.NEXT_PUBLIC_SUPABASE_URL and settings.NEXT_PUBLIC_SUPABASE_ANON_KEY:
    try:
        supabase = create_client(
            settings.NEXT_PUBLIC_SUPABASE_URL,
            settings.NEXT_PUBLIC_SUPABASE_ANON_KEY,
            # 권한 문제가 있다면 Service Role Key 사용:
            # settings.SUPABASE_SERVICE_ROLE_KEY,
        )
        logger.info("✅ Supabase 클라이언트 초기화 완료")
    except Exception as e:
        logger.warning(f"⚠️ Supabase 클라이언트 초기화 실패: {e}")
else:
    logger.warning("ℹ️ Supabase 환경 변수가 설정되지 않음 (Storage 기능 비활성화)")

# 환경 변수에서 버킷 이름 가져오기
BUCKET_NAME = "yb_test_storage"


async def load_uploaded_image(image_path: str) -> bytes:
    """
    Supabase Storage에서 image를 반환합니다.

    Args:
        image_path: 이미지 path

    Returns:
        dict: bytes

    Raises:
        Exception: Storage 업로드 실패 시
    """
    # Supabase가 설정되지 않은 경우 에러
    if supabase is None:
        raise Exception(
            "Supabase Storage가 설정되지 않았습니다. "
            "환경 변수를 설정하세요."
        )

    try:
        # filename 파라미터를 사용하여 업로드
        bytes = supabase.storage.from_(BUCKET_NAME).download(
            path=f"/{image_path}",
        )
        return bytes

    except Exception as e:
        error_msg = str(e)
        logger.error("❌ Supabase Storage 업로드 실패 ")

        # RLS 정책 위반인 경우
        if "row-level security policy" in error_msg.lower():
            raise Exception(
                "Supabase Storage 권한 오류: RLS 정책을 확인하세요. "
                "Storage 버킷에 대한 INSERT 권한이 필요합니다."
            )
        # 버킷이 없는 경우
        elif "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            raise Exception(f"Storage 버킷 '{BUCKET_NAME}'을 찾을 수 없습니다.")
        # 기타 에러
        else:
            raise Exception(f"파일 업로드 실패: {error_msg}")


async def save_uploaded_image(
    image_data: bytes, filename: str, content_type: Optional[str]
) -> ImageResponse:
    """
    업로드된 이미지를 Supabase Storage에 저장하고 URL을 반환합니다.

    Args:
        file: 업로드된 파일 객체
        filename: 저장할 파일명

    Returns:
        dict: 업로드 응답과 public URL

    Raises:
        Exception: Storage 업로드 실패 시
    """
    # Supabase가 설정되지 않은 경우 에러
    if supabase is None:
        raise Exception(
            "Supabase Storage가 설정되지 않았습니다. "
            "환경 변수를 설정하세요."
        )

    try:
        now = datetime.now()
        formatted_date = now.strftime("%Y-%m-%d")

        contents = image_data

        unique_file_name = str(uuid.uuid4()) + "_" + filename

        # filename 파라미터를 사용하여 업로드
        response = supabase.storage.from_(BUCKET_NAME).upload(
            path=f"uploads/{formatted_date}/{unique_file_name}",
            file=contents,
            file_options={
                "content-type": str(content_type or "application/octet-stream")
            },
        )

        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(
            f"uploads/{formatted_date}/{unique_file_name}"
        )

        return ImageResponse(private_img=response.fullPath, public_img=public_url)

    except Exception as e:
        error_msg = str(e)
        logger.error("❌ Supabase Storage 업로드 실패 ")

        # RLS 정책 위반인 경우
        if "row-level security policy" in error_msg.lower():
            raise Exception(
                "Supabase Storage 권한 오류: RLS 정책을 확인하세요. "
                "Storage 버킷에 대한 INSERT 권한이 필요합니다."
            )
        # 버킷이 없는 경우
        elif "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            raise Exception(f"Storage 버킷 '{BUCKET_NAME}'을 찾을 수 없습니다.")
        # 기타 에러
        else:
            raise Exception(f"파일 업로드 실패: {error_msg}")


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
