# app/core/redis_client.py

from typing import Optional

from redis.asyncio import ConnectionPool, Redis

from ..config import settings


class RedisClient:
    _instance: Optional[Redis] = None
    _pool: Optional[ConnectionPool] = None

    @classmethod
    async def init(cls) -> Redis:
        """Connection Pool로 초기화"""
        if not cls._pool:
            cls._pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                max_connections=50,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 1,  # TCP_KEEPINTVL
                    3: 5,  # TCP_KEEPCNT
                },
            )
            cls._instance = Redis(connection_pool=cls._pool)
            # Redis 연결 확인 (비동기 메서드, Pylance 타입 추론 이슈로 ignore 추가)
            await cls._instance.ping()  # type: ignore[misc]

        assert cls._instance is not None
        return cls._instance

    @classmethod
    async def close(cls):
        """연결 종료"""
        if cls._instance:
            await cls._instance.close()
        if cls._pool:
            await cls._pool.disconnect()

    @classmethod
    def get_instance(cls) -> Redis:
        """Dependency Injection용"""
        if not cls._instance:
            raise RuntimeError("Redis not initialized")
        return cls._instance


# Dependency
async def get_redis() -> Redis:
    return RedisClient.get_instance()
