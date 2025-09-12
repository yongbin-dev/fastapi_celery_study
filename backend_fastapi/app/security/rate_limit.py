# app/security/rate_limit.py
"""
Rate Limiting 구현
"""

import time
from typing import Dict, Optional
from fastapi import Request, HTTPException
import redis.asyncio as redis

from ..core.config import settings


class RateLimiter:
    """Rate Limiting 클래스"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_cache: Dict[str, Dict] = {}  # Redis가 없을 때 사용

    async def is_allowed(
        self,
        identifier: str,
        limit: int,
        window: int  # seconds
    ) -> tuple[bool, dict]:
        """
        Rate limit 확인
        
        Args:
            identifier: 식별자 (IP, 사용자 ID 등)
            limit: 허용 요청 수
            window: 시간 윈도우 (초)
        
        Returns:
            (허용여부, 상태정보)
        """
        current_time = time.time()
        key = f"rate_limit:{identifier}"

        if self.redis_client:
            return await self._check_redis_rate_limit(key, limit, window, current_time)
        else:
            return self._check_local_rate_limit(key, limit, window, current_time)

    async def _check_redis_rate_limit(
        self, key: str, limit: int, window: int, current_time: float
    ) -> tuple[bool, dict]:
        """Redis를 사용한 rate limit 확인"""
        pipe = self.redis_client.pipeline()
        
        # 윈도우 시작 시간
        window_start = current_time - window
        
        # 오래된 기록 삭제
        pipe.zremrangebyscore(key, 0, window_start)
        
        # 현재 요청 수 확인
        pipe.zcard(key)
        
        # 현재 시간 추가
        pipe.zadd(key, {str(current_time): current_time})
        
        # TTL 설정
        pipe.expire(key, window)
        
        results = await pipe.execute()
        current_requests = results[1]
        
        status = {
            "requests": current_requests,
            "limit": limit,
            "window": window,
            "reset_time": current_time + window
        }
        
        return current_requests <= limit, status

    def _check_local_rate_limit(
        self, key: str, limit: int, window: int, current_time: float
    ) -> tuple[bool, dict]:
        """로컬 메모리를 사용한 rate limit 확인"""
        if key not in self.local_cache:
            self.local_cache[key] = {"requests": [], "reset_time": current_time + window}
        
        cache_entry = self.local_cache[key]
        
        # 윈도우 시작 시간
        window_start = current_time - window
        
        # 오래된 요청 제거
        cache_entry["requests"] = [
            req_time for req_time in cache_entry["requests"] 
            if req_time > window_start
        ]
        
        # 현재 요청 추가
        cache_entry["requests"].append(current_time)
        
        status = {
            "requests": len(cache_entry["requests"]),
            "limit": limit,
            "window": window,
            "reset_time": cache_entry["reset_time"]
        }
        
        return len(cache_entry["requests"]) <= limit, status


# 전역 Rate Limiter 인스턴스
rate_limiter = RateLimiter()


class RateLimitMiddleware:
    """Rate Limit 미들웨어"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

    async def __call__(self, request: Request, call_next):
        """미들웨어 실행"""
        # 클라이언트 IP 주소 획득
        client_ip = self._get_client_ip(request)
        
        # 분당 요청 제한 확인
        allowed_minute, status_minute = await rate_limiter.is_allowed(
            f"minute:{client_ip}",
            self.requests_per_minute,
            60
        )
        
        # 시간당 요청 제한 확인
        allowed_hour, status_hour = await rate_limiter.is_allowed(
            f"hour:{client_ip}",
            self.requests_per_hour,
            3600
        )
        
        if not allowed_minute:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "분당 요청 한도를 초과했습니다",
                    "limit": self.requests_per_minute,
                    "reset_time": status_minute["reset_time"]
                }
            )
        
        if not allowed_hour:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "시간당 요청 한도를 초과했습니다",
                    "limit": self.requests_per_hour,
                    "reset_time": status_hour["reset_time"]
                }
            )
        
        # 요청 처리
        response = await call_next(request)
        
        # Rate limit 정보를 헤더에 추가
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            self.requests_per_minute - status_minute["requests"]
        )
        response.headers["X-RateLimit-Reset-Minute"] = str(int(status_minute["reset_time"]))
        
        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """클라이언트 IP 주소 획득"""
        # Proxy 헤더 확인
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


# 특정 엔드포인트를 위한 Rate Limit 데코레이터
def rate_limit(requests: int, window: int):
    """Rate limit 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Request 객체 찾기
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                client_ip = RateLimitMiddleware._get_client_ip(request)
                allowed, status = await rate_limiter.is_allowed(
                    f"endpoint:{func.__name__}:{client_ip}",
                    requests,
                    window
                )
                
                if not allowed:
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "message": f"API 호출 한도를 초과했습니다",
                            "limit": requests,
                            "window": window,
                            "reset_time": status["reset_time"]
                        }
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator