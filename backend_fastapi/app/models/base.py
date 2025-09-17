
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """모든 모델의 기본 클래스 - 공통 타임스탬프 필드 포함 (서울 시간대)"""
    
    created_at = Column(
        DateTime(timezone=True), 
        default=datetime.now,
        nullable=False,
        comment="생성 시간 (서울)"
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
        comment="수정 시간 (서울)"
    )