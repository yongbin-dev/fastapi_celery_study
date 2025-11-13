"""Supabase Storage 구현"""

from typing import Optional

from ..config import settings
from ..core.logging import get_logger
from ..schemas.common import ImageResponse
from .storage_base import StorageProvider

logger = get_logger(__name__)


class SupabaseStorage(StorageProvider):
    """Supabase Storage 구현"""

    def __init__(self, bucket_name: str = "yb_test_storage"):
        self.bucket_name = bucket_name
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Supabase 클라이언트 초기화"""
        if (
            not settings.NEXT_PUBLIC_SUPABASE_URL
            or not settings.NEXT_PUBLIC_SUPABASE_ANON_KEY
        ):
            logger.warning("⚠️ Supabase 환경 변수가 설정되지 않음")
            return

        try:
            from supabase import create_client

            self._client = create_client(
                settings.NEXT_PUBLIC_SUPABASE_URL,
                settings.NEXT_PUBLIC_SUPABASE_ANON_KEY,
            )
            logger.info("✅ Supabase 클라이언트 초기화 완료")
        except Exception as e:
            logger.warning(f"⚠️ Supabase 클라이언트 초기화 실패: {e}")

    async def download(self, path: str) -> bytes:
        """Supabase Storage에서 파일 다운로드"""
        if self._client is None:
            raise Exception("Supabase Storage가 설정되지 않았습니다.")

        try:
            # 경로 정규화
            # 1. 슬래시로 시작하면 제거
            normalized_path = (
                "/".join(path.split("/")[1:]) if path.startswith("/") else path
            )

            # 2. 버킷 이름이 경로에 포함되어 있으면 제거
            if normalized_path.startswith(f"{self.bucket_name}/"):
                normalized_path = normalized_path[len(self.bucket_name) + 1 :]

            logger.debug(f"이미지 다운로드 시도: {normalized_path}")

            image_data = self._client.storage.from_(self.bucket_name).download(
                path=normalized_path
            )
            logger.info(f"✅ 이미지 다운로드 성공: {len(image_data)} bytes")
            return image_data

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Supabase Storage 다운로드 실패: {error_msg}")

            if "row-level security policy" in error_msg.lower():
                raise Exception(
                    "Supabase Storage 권한 오류: RLS 정책을 확인하세요. "
                    "Storage 버킷에 대한 READ 권한이 필요합니다."
                )
            elif (
                "not found" in error_msg.lower()
                or "does not exist" in error_msg.lower()
            ):
                raise Exception(
                    f"Storage 버킷 '{self.bucket_name}' 또는 파일을 찾을 수 없습니다: "
                    f"{path}"
                )
            else:
                raise Exception(f"파일 로드 실패: {error_msg}")

    async def upload(
        self, file_data: bytes, path: str, content_type: Optional[str] = None
    ) -> ImageResponse:
        """Supabase Storage에 파일 업로드"""
        if self._client is None:
            raise Exception("Supabase Storage가 설정되지 않았습니다.")

        try:
            response = self._client.storage.from_(self.bucket_name).upload(
                path=path,
                file=file_data,
                file_options={
                    "content-type": str(content_type or "application/octet-stream")
                },
            )

            public_url = self._client.storage.from_(self.bucket_name).get_public_url(
                path
            )

            return ImageResponse(private_img=response.fullPath, public_img=public_url)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Supabase Storage 업로드 실패: {error_msg}")

            if "row-level security policy" in error_msg.lower():
                raise Exception(
                    "Supabase Storage 권한 오류: RLS 정책을 확인하세요. "
                    "Storage 버킷에 대한 INSERT 권한이 필요합니다."
                )
            elif (
                "not found" in error_msg.lower()
                or "does not exist" in error_msg.lower()
            ):
                raise Exception(
                    f"Storage 버킷 '{self.bucket_name}'을 찾을 수 없습니다."
                )
            else:
                raise Exception(f"파일 업로드 실패: {error_msg}")

    def get_public_url(self, path: str) -> str:
        """Public URL 조회"""
        if self._client is None:
            raise Exception("Supabase Storage가 설정되지 않았습니다.")
        return self._client.storage.from_(self.bucket_name).get_public_url(path)
