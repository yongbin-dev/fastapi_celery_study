"""파일 처리 유틸리티 - Storage 팩토리 및 레거시 함수"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from ..config import settings
from ..schemas.common import ImageResponse
from .storage_base import StorageProvider
from .supabase_storage import SupabaseStorage


# Storage Provider Factory
def get_storage_provider(provider_type: str = "supabase") -> StorageProvider:
    """
    Storage Provider 팩토리 함수 (FastAPI Depends에서 사용 가능)

    Args:
        provider_type: 'supabase' 또는 'minio'

    Returns:
        StorageProvider 인스턴스
    """
    if provider_type == "supabase":
        return SupabaseStorage()
    # elif provider_type == "minio":
    #     return MinIOStorage()
    else:
        raise ValueError(f"지원하지 않는 Storage Provider: {provider_type}")


# 전역 Storage 인스턴스 (기본값: Supabase)
_default_storage: Optional[StorageProvider] = None


def get_default_storage() -> StorageProvider:
    """
    기본 Storage Provider 반환 (FastAPI Depends에서 사용)

    환경 변수 STORAGE_PROVIDER로 제어 (기본값: supabase)
    """
    global _default_storage

    if _default_storage is None:
        provider_type = getattr(settings, "STORAGE_PROVIDER", "supabase")
        _default_storage = get_storage_provider(provider_type)

    return _default_storage


# 하위 호환성을 위한 레거시 함수들
async def load_uploaded_image(image_path: str) -> bytes:
    """
    [레거시] 이미지 로드 (하위 호환성)

    새 코드에서는 get_default_storage()를 Depends로 주입받아 사용하세요.
    """
    storage = get_default_storage()
    return await storage.download(image_path)


async def save_uploaded_image(
    image_data: bytes, filename: str, content_type: Optional[str]
) -> ImageResponse:
    """
    [레거시] 이미지 저장 (uploads/{filename})

    새 코드에서는 get_default_storage()를 Depends로 주입받아 사용하세요.
    """
    storage = get_default_storage()
    path = f"uploads/{filename}"
    return await storage.upload(image_data, path, content_type)


async def save_uploaded_file(
    image_data: bytes, filename: str, content_type: Optional[str]
) -> ImageResponse:
    """
    [레거시] 파일 저장 (uploads/{YYYYMMDD}/{filename})

    새 코드에서는 get_default_storage()를 Depends로 주입받아 사용하세요.
    """
    storage = get_default_storage()
    now = datetime.now()
    formatted_date = now.strftime("%Y%m%d")
    path = f"uploads/{formatted_date}/{filename}"
    return await storage.upload(image_data, path, content_type)


# 유틸리티 함수들
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
