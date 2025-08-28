# app/core/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# 비동기 엔진 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    pool_size=20,
    max_overflow=0,
)

# 비동기 세션 팩토리
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base 클래스
Base = declarative_base()


async def get_db():
    """
    데이터베이스 세션 의존성
    FastAPI endpoint에서 Depends(get_db)로 사용
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    데이터베이스 테이블 초기화
    앱 시작시 호출 (선택사항)
    """
    async with engine.begin() as conn:
        # 모든 테이블 생성 (개발시에만 사용, 프로덕션에서는 마이그레이션 사용)
        await conn.run_sync(Base.metadata.create_all)
        pass


async def close_db():
    """
    데이터베이스 연결 종료
    앱 종료시 호출
    """
    await engine.dispose()