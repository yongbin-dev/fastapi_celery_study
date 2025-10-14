# app/models/ocr_text_box.py
from sqlalchemy import Column, Float, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from .base import Base


class OCRTextBox(Base):
    """
    OCR 텍스트 박스 상세 테이블
    - OCR로 추출된 개별 텍스트 박스 정보
    """

    __tablename__ = "ocr_text_boxes"

    # 기본 필드
    id = Column(Integer, primary_key=True, comment="고유 식별자")
    ocr_execution_id = Column(
        Integer,
        ForeignKey("ocr_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="OCR 실행 ID",
    )

    # 텍스트 박스 정보
    text = Column(Text, nullable=False, comment="추출된 텍스트")
    confidence = Column(Float, nullable=False, comment="신뢰도 점수 (0.0 ~ 1.0)")
    bbox = Column(
        JSON,
        nullable=False,
        comment="바운딩 박스 좌표 JSON [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]",
    )

    # 관계 정의
    ocr_execution = relationship("OCRExecution", back_populates="text_boxes")

    # 인덱스 정의
    __table_args__ = (
        Index("idx_ocr_text_boxes_execution_id", "ocr_execution_id"),
        Index("idx_ocr_text_boxes_confidence", "confidence"),
    )

    def __repr__(self):
        text_preview = str(self.text)[:20]
        return (
            f"<OCRTextBox(id={self.id}, "
            f"text='{text_preview}...', "
            f"confidence={self.confidence:.2f})>"
        )
