# app/domains/ocr/schemas/ocr_db.py
"""OCR DB 스키마"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from shared.schemas.ocr_text_box import OCRTextBoxCreate


class OCRExtractDTO(BaseModel):
    """OCR 텍스트 추출 응답 스키마"""

    status: str = Field(..., description="태스크 상태")
    error: Optional[str] = Field(default=None, description="에러")
    text_boxes: List[OCRTextBoxCreate] = Field(
        default=[], description="추출된 텍스트 박스 목록"
    )

    model_config = ConfigDict(from_attributes=True)
