from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db


async def get_database() -> AsyncSession:
    async for session in get_db():
        yield session