
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

# 네이밍 컨벤션 설정
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)

# 서울 시간대 설정
SEOUL_TZ = ZoneInfo('Asia/Seoul')

def seoul_now():
    """현재 서울 시간 반환"""
    return datetime.now(SEOUL_TZ)

class Base(DeclarativeBase):
    """모든 모델의 기본 클래스 - 공통 타임스탬프 필드 포함 (서울 시간대)"""
    
    created_at = Column(
        DateTime(timezone=True), 
        default=seoul_now,
        nullable=False,
        comment="생성 시간 (서울)"
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        default=seoul_now,
        onupdate=seoul_now,
        nullable=False,
        comment="수정 시간 (서울)"
    )