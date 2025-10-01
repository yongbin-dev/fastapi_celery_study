# app/models/ocr_execution.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class OCRExecution(Base):
    """
    OCR 실행 정보 테이블
    - OCR 작업의 메타데이터 저장 (이미지 경로, 상태, 에러)
    """

    __tablename__ = "ocr_executions"

    # 기본 필드
    id = Column(Integer, primary_key=True, comment="고유 식별자")
    chain_id = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        comment="Celery chain ID (선택적)",
    )

    image_path = Column(String(255), unique=True, index=True, comment="이미지 경로")
    # OCR 실행 상태
    status = Column(
        String(50),
        nullable=False,
        index=True,
        comment="처리 상태 (success/failed)",
    )

    error = Column(Text, nullable=True, comment="에러 메시지 (실패 시)")

    # 관계 정의
    text_boxes = relationship(
        "OCRTextBox",
        back_populates="ocr_execution",
        cascade="all, delete-orphan",
        lazy="selectin",  # N+1 쿼리 방지
    )

    def __repr__(self):
        boxes_count = len(self.text_boxes)
        return (
            f"<OCRExecution(id={self.id}, "
            f"status={self.status}, "
            f"boxes={boxes_count})>"
        )
