
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OCRExecutionCreate(BaseModel):
    """OCR 실행 정보 생성 스키마"""

    chain_id: Optional[str] = Field(None, description="Celery chain ID (선택적)")
    image_path: str = Field(..., description="이미지 파일 경로")
    public_path: str = Field(..., description="이미지 공개 경로")
    status: str = Field(..., description="처리 상태 (success/failed)")
    error: Optional[str] = Field(None, description="에러 메시지")

    model_config = ConfigDict(from_attributes=True)
