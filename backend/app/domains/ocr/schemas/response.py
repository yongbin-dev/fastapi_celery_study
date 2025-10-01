# app/domains/ocr/schemas/response.py
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class TextBoxDTO(BaseModel):
    """텍스트 박스 DTO"""

    text: str = Field(..., description="추출된 텍스트")
    confidence: float = Field(..., description="신뢰도 점수 (0.0 ~ 1.0)")
    bbox: List[List[float]] = Field(
        ..., description="바운딩 박스 좌표 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]"
    )
    model_config = ConfigDict(from_attributes=True)


class OCRResultDTO(BaseModel):
    """OCR 실행 결과 DTO"""

    text_boxes: List[TextBoxDTO] = Field(
        default_factory=list, description="추출된 텍스트 박스 목록"
    )
    full_text: str = Field(default="", description="전체 추출 텍스트")
    status: Literal["success", "failed"] = Field(..., description="처리 상태")
    error: str | None = Field(default=None, description="에러 메시지 (실패 시)")


# 기존 스키마 (하위 호환성)
class OCRTextBox(BaseModel):
    """OCR 텍스트 박스 (deprecated: TextBoxDTO 사용 권장)"""

    text: str = Field(..., description="추출된 텍스트")
    confidence: float = Field(..., description="신뢰도 점수")
    bbox: List[List[float]] = Field(..., description="바운딩 박스 좌표")
    model_config = ConfigDict(from_attributes=True)


class OCRExtractResponse(BaseModel):
    """OCR 텍스트 추출 응답 스키마"""

    chain_id: Optional[str] = Field(
        ...,
        description="Celery 태스크 ID",
    )
    status: str = Field(..., description="태스크 상태")
    image_path: Optional[str] = Field(default=None, description="전체 추출 텍스트")
    error: Optional[str] = Field(default=None, description="에러")
    text_boxes: Optional[List[OCRTextBox]] = Field(
        default=None, description="추출된 텍스트 박스 목록"
    )

    model_config = ConfigDict(from_attributes=True)
