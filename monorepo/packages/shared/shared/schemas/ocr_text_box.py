from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OCRTextBoxCreate(BaseModel):
    """텍스트 박스 생성 스키마"""

    ocr_execution_id: Optional[int] = Field(default=None, description="OCR 실행 ID")
    text: str = Field(..., description="추출된 텍스트")
    confidence: float = Field(..., description="신뢰도 점수 (0.0 ~ 1.0)")
    bbox: List[List[float]] = Field(
        ..., description="바운딩 박스 좌표 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]"
    )

    model_config = ConfigDict(from_attributes=True)
