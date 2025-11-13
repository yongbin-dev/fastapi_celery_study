"""스토리지 추상 클래스"""

from abc import ABC, abstractmethod
from typing import Optional

from ..schemas.common import ImageResponse


class StorageProvider(ABC):
    """스토리지 제공자 추상 클래스"""

    @abstractmethod
    async def download(self, path: str) -> bytes:
        """파일 다운로드"""
        pass

    @abstractmethod
    async def upload(
        self, file_data: bytes, path: str, content_type: Optional[str] = None
    ) -> ImageResponse:
        """파일 업로드"""
        pass

    @abstractmethod
    def get_public_url(self, path: str) -> str:
        """Public URL 조회"""
        pass
