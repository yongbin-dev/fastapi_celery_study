# app/core/database.py

import logging
import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine

from typing import cast

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from functools import lru_cache
from app.config import settings
from app.models.base import Base

# 로깅 설정
logger = logging.getLogger(__name__)

# 공통 엔진 설정
COMMON_ENGINE_CONFIG = {
    "echo": settings.DB_ECHO,
    "pool_size": settings.DB_POOL_SIZE,
    "max_overflow": settings.DB_MAX_OVERFLOW,
    "pool_pre_ping": settings.DB_POOL_PRE_PING,
    "pool_recycle": settings.DB_POOL_RECYCLE,
}


# 데이터베이스 연결 관리 클래스
class DatabaseManager:
    """
    데이터베이스 엔진 및 세션을 관리하는 클래스
    FastAPI의 의존성 주입을 통해 싱글톤으로 사용됨
    """

    def __init__(self):
        # 비동기 엔진 생성
        database_url = settings.DATABASE_URL
        self.async_engine: AsyncEngine = create_async_engine(
            database_url,
            future=True,
            connect_args={
                "server_settings": {"timezone": settings.DB_TIMEZONE},
                "command_timeout": settings.DB_CONNECT_TIMEOUT,
            },
            **COMMON_ENGINE_CONFIG,
        )

        # 비동기 세션 팩토리
        self.AsyncSessionLocal = sessionmaker(
            bind=self.async_engine, class_=AsyncSession, expire_on_commit=False  # type: ignore
        )  # type: ignore

        # 동기 엔진 생성 (Celery signal용)
        sync_database_url = database_url.replace(
            "postgresql+asyncpg://", "postgresql://"
        )
        self.sync_engine = create_engine(
            sync_database_url,
            connect_args={"options": f"-c timezone={settings.DB_TIMEZONE}"},
            **COMMON_ENGINE_CONFIG,
        )

        # 동기 세션 팩토리
        self.SyncSessionLocal = sessionmaker(
            bind=self.sync_engine, class_=Session, expire_on_commit=False
        )

        # 헬스체크용 별도 엔진
        self.health_check_engine: AsyncEngine = create_async_engine(
            database_url,
            future=True,
            echo=False,
            pool_size=settings.DB_HEALTH_CHECK_POOL_SIZE,
            max_overflow=0,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "server_settings": {"timezone": settings.DB_TIMEZONE},
                "command_timeout": 5,
            },
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        비동기 세션 컨텍스트 매니저
        """

        session = cast(AsyncSession, self.AsyncSessionLocal())

        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @contextmanager
    def get_sync_session(self) -> Generator[Session, None, None]:
        """
        동기 세션 컨텍스트 매니저 (Celery용)
        """
        session: Session = self.SyncSessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def health_check(self) -> bool:
        try:
            async with self.health_check_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.warning(f"데이터베이스 헬스체크 실패: {str(e)}")
            return False

    async def dispose(self) -> None:
        logger.info("데이터베이스 연결 종료 중...")
        await self.async_engine.dispose()
        self.sync_engine.dispose()
        await self.health_check_engine.dispose()
        logger.info("데이터베이스 연결 종료 완료")


# 싱글톤으로 데이터베이스 매니저 인스턴스 생성
@lru_cache
def get_db_manager() -> DatabaseManager:
    return DatabaseManager()


# 의존성 주입 함수
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    max_retries = 3
    retry_delay = 0.1
    db_manager = get_db_manager()

    for attempt in range(max_retries):
        try:
            async with db_manager.get_session() as session:
                # 연결 테스트
                await session.execute(text("SELECT 1"))
                yield session
                return
        except (DisconnectionError, SQLAlchemyError) as e:
            logger.warning(
                f"데이터베이스 연결 실패 (시도 {attempt + 1}/{max_retries}): {str(e)[:100]}"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (2**attempt))
                continue
            else:
                logger.error(f"데이터베이스 연결 최대 재시도 횟수 초과: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"예기치 못한 데이터베이스 에러: {str(e)}")
            raise


# 초기화 및 종료 함수
async def init_db() -> None:
    db_manager = get_db_manager()
    try:
        # 타임아웃 설정으로 빠른 실패
        async with asyncio.timeout(settings.DB_CONNECT_TIMEOUT):
            async with db_manager.async_engine.begin() as conn:
                # 연결 테스트 먼저 수행
                await conn.execute(text("SELECT 1"))
                logger.info("🔗 데이터베이스 연결 테스트 성공")

                if settings.environment == "development":
                    logger.info("개발 환경: 데이터베이스 테이블 생성 중...")
                    # await conn.run_sync(Base.metadata.drop_all)
                    await conn.run_sync(Base.metadata.create_all)
                    logger.info("데이터베이스 테이블 생성 완료")
                else:
                    logger.info("프로덕션 환경: 테이블 생성 건너뜀 (마이그레이션 사용)")
    except asyncio.TimeoutError:
        logger.error(f"데이터베이스 연결 타임아웃 ({settings.DB_CONNECT_TIMEOUT}초)")
        raise
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {str(e)}")
        raise


async def close_db() -> None:
    db_manager = get_db_manager()
    await db_manager.dispose()
