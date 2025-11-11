# app/services/redis_service.py

from typing import Optional

import redis

from ..config import settings


class RedisService:
    """Redis를 사용한 파이프라인 상태 관리 구현체"""

    _redis_client: Optional[redis.Redis] = None

    def __init__(
        self,
        redis_host: str,
        redis_port: int = 6379,
        redis_db: int = 0,
    ):
        self._redis_client = None
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db

    def get_redis_client(self) -> redis.Redis:
        """Redis 클라이언트 싱글톤 패턴으로 관리"""
        if not self._redis_client:
            self._redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
            )
        return self._redis_client


def get_redis_service():
    return RedisService(
        redis_host=settings.REDIS_HOST,
        redis_port=settings.REDIS_PORT,
        redis_db=int(settings.REDIS_DB),
    )


def get_redis_client_sync():
    return RedisService(
        redis_host=settings.REDIS_HOST,
        redis_port=settings.REDIS_PORT,
        redis_db=int(settings.REDIS_DB),
    ).get_redis_client()
