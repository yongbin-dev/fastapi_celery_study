# app/domains/ocr/schemas/ocr_db.py
"""OCR DB 스키마"""
from typing import List, Optional

from pydantic import BaseModel, Field


class OCRTextBoxCreate(BaseModel):
    """텍스트 박스 생성 스키마"""

    ocr_execution_id: int = Field(..., description="OCR 실행 ID")
    text: str = Field(..., description="추출된 텍스트")
    confidence: float = Field(..., description="신뢰도 점수 (0.0 ~ 1.0)")
    bbox: List[List[float]] = Field(
        ..., description="바운딩 박스 좌표 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]"
    )


class OCRExecutionCreate(BaseModel):
    """OCR 실행 정보 생성 스키마"""

    chain_id: Optional[str] = Field(None, description="Celery chain ID (선택적)")
    image_path: str = Field(..., description="이미지 파일 경로")
    status: str = Field(..., description="처리 상태 (success/failed)")
    error: Optional[str] = Field(None, description="에러 메시지")


class OCRTextBoxRead(BaseModel):
    """텍스트 박스 읽기 스키마"""

    id: int
    ocr_execution_id: int
    text: str
    confidence: float
    bbox: List[List[float]]

    class Config:
        from_attributes = True


class OCRExecutionRead(BaseModel):
    """OCR 실행 정보 읽기 스키마"""

    id: int
    chain_id: Optional[str]
    image_path: str
    status: str
    error: Optional[str]
    text_boxes: List[OCRTextBoxRead] = []

    class Config:
        from_attributes = True
