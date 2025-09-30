# app/domains/ocr/schemas/request.py
from pydantic import BaseModel, Field
from typing import Optional


class OCRExtractRequest(BaseModel):
    """OCR 텍스트 추출 요청 스키마"""

    image_path: str = Field(..., description="이미지 파일 경로", min_length=1)
    language: Optional[str] = Field(default="korean", description="추출할 언어")
    use_angle_cls: Optional[bool] = Field(default=True, description="각도 분류 사용 여부")
    confidence_threshold: Optional[float] = Field(
        default=0.5, ge=0.0, le=1.0, description="신뢰도 임계값"
    )