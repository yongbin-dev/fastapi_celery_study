# app/domains/ocr/schemas/ocr_db.py
"""OCR DB 스키마"""

from typing import List, Optional

from pydantic import Field

from shared.schemas import CustomBaseModel, OCRTextBoxCreate


class OCRExtractDTO(CustomBaseModel):
    """OCR 텍스트 추출 응답 스키마"""

    status: str = Field(..., description="태스크 상태")
    error: Optional[str] = Field(default=None, description="에러")
    text_boxes: List[OCRTextBoxCreate] = Field(
        default=[], description="추출된 텍스트 박스 목록"
    )
