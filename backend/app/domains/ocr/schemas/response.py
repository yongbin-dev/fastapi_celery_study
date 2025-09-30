# app/domains/ocr/schemas/response.py
from pydantic import BaseModel, Field
from typing import List, Optional


class OCRTextBox(BaseModel):
    """OCR 텍스트 박스"""

    text: str = Field(..., description="추출된 텍스트")
    confidence: float = Field(..., description="신뢰도 점수")
    bbox: List[List[float]] = Field(..., description="바운딩 박스 좌표")


class OCRExtractResponse(BaseModel):
    """OCR 텍스트 추출 응답 스키마"""

    task_id: str = Field(..., description="Celery 태스크 ID")
    status: str = Field(..., description="태스크 상태")
    text_boxes: Optional[List[OCRTextBox]] = Field(default=None, description="추출된 텍스트 박스 목록")
    full_text: Optional[str] = Field(default=None, description="전체 추출 텍스트")