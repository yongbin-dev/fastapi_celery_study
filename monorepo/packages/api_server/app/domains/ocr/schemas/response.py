# app/domains/ocr/schemas/response.py
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from shared.schemas.ocr_db import OCRTextBoxCreate


class OCRResultDTO(BaseModel):
    """OCR 실행 결과 DTO"""

    id: int = Field(default=0, description="ID")
    public_path: Optional[str] = Field(default="", description="이미지 공개  경로")
    text_boxes: List[OCRTextBoxCreate] = Field(
        default_factory=list, description="추출된 텍스트 박스 목록"
    )
    full_text: str = Field(default="", description="전체 추출 텍스트")
    status: Literal["success", "failed"] = Field(..., description="처리 상태")
    error: str | None = Field(default=None, description="에러 메시지 (실패 시)")

    model_config = ConfigDict(from_attributes=True)
