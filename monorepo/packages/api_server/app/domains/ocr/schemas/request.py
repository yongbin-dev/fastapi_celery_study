# app/domains/ocr/schemas/request.py
from pydantic import BaseModel, Field


class OCRRequestDTO(BaseModel):
    """OCR 요청 DTO"""

    image_data: bytes = Field(..., description="이미지 바이너리 데이터")
    language: str = Field(default="korean", description="추출할 언어")
    confidence_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="신뢰도 임계값"
    )
    use_angle_cls: bool = Field(default=True, description="각도 분류 사용 여부")
