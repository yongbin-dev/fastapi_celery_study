# app/core/redis_client.py

from functools import lru_cache
import redis
from typing import Optional

from .config import settings


@lru_cache()
def get_redis_client(
    host: Optional[str] = None,
    port: Optional[int] = None,
    db: int = 0,
    decode_responses: bool = True
) -> redis.Redis:
    """
    Redis 클라이언트 싱글톤
    
    애플리케이션당 하나의 인스턴스만 생성하여 연결을 재사용합니다.
    여러 서비스에서 공통으로 사용할 수 있도록 설계되었습니다.
    
    Args:
        host: Redis 서버 호스트 (기본: settings.REDIS_HOST)
        port: Redis 서버 포트 (기본: settings.REDIS_PORT) 
        db: Redis 데이터베이스 번호 (기본: 0)
        decode_responses: 응답을 문자열로 디코딩할지 여부 (기본: True)
    
    Returns:
        Redis 클라이언트 인스턴스
        
    Example:
        ```python
        from app.core.redis_client import get_redis_client
        
        # 기본 설정으로 사용
        redis_client = get_redis_client()
        
        # 사용자 정의 설정
        redis_client = get_redis_client(db=1, decode_responses=False)
        ```
    """
    return redis.Redis(
        host=host or settings.REDIS_HOST,
        port=port or settings.REDIS_PORT,
        db=db,
        decode_responses=decode_responses
    )


@lru_cache()
def get_redis_cache_client() -> redis.Redis:
    """캐시용 Redis 클라이언트 (DB 1 사용)"""
    return get_redis_client(db=1)


@lru_cache() 
def get_redis_session_client() -> redis.Redis:
    """세션용 Redis 클라이언트 (DB 2 사용)"""
    return get_redis_client(db=2)


# 기본 Redis 클라이언트 인스턴스 (하위 호환성)
def get_default_redis_client() -> redis.Redis:
    """기본 Redis 클라이언트 (DB 0 사용)"""
    return get_redis_client()