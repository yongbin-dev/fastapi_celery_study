"""파이프라인 컨텍스트 캐시 서비스

Redis를 사용하여 PipelineContext를 저장/조회하는 서비스
"""

import json
from typing import Optional

import redis

from ..core.logging import get_logger
from ..service.redis_service import get_redis_service
from .context import PipelineContext

logger = get_logger(__name__)


class PipelineCacheService:
    """파이프라인 컨텍스트 Redis 캐시 서비스"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Args:
            redis_client: Redis 클라이언트 (None일 경우 기본 클라이언트 사용)
        """
        self.redis_client = redis_client or get_redis_service().get_redis_client()

    def _get_key(self, batch_id: str, chain_id: str) -> str:
        """Redis 키 생성

        Args:
            batch_id: 배치 ID
            chain_id: 체인 ID

        Returns:
            Redis 키
        """
        return f"pipeline:batch:{batch_id}:chain:{chain_id}"

    def save_context(self, context: PipelineContext, ttl: int = 86400) -> None:
        """Context를 Redis에 저장

        Args:
            context: 파이프라인 컨텍스트
            ttl: Time To Live (초, 기본 24시간)
        """
        key = self._get_key(context.batch_id, context.chain_id)
        self.redis_client.set(key, context.model_dump_json(), ex=ttl)
        logger.debug(f"✅ 컨텍스트 저장: {key} (TTL: {ttl}s)")

    def load_context(self, batch_id: str, chain_id: str) -> PipelineContext:
        """Redis에서 Context 로드

        Args:
            batch_id: 배치 ID
            chain_id: 체인 ID

        Returns:
            파이프라인 컨텍스트

        Raises:
            ValueError: Context가 Redis에 없을 때
        """
        key = self._get_key(batch_id, chain_id)
        data = self.redis_client.get(key)

        if not data:
            raise ValueError(f"Context not found in Redis: {key}")

        # JSON 문자열을 딕셔너리로 파싱
        if isinstance(data, str):
            data_dict = json.loads(data)
        else:
            data_dict = data

        logger.debug(f"✅ 컨텍스트 로드: {key}")
        return PipelineContext(**data_dict)  # type: ignore

    def load_all_by_batch_id(self, batch_id: str) -> list[PipelineContext]:
        """batch_id로 모든 Context 조회

        Args:
            batch_id: 배치 ID

        Returns:
            파이프라인 컨텍스트 리스트

        Raises:
            ValueError: batch_id에 해당하는 Context가 없을 때
        """
        pattern = f"pipeline:batch:{batch_id}:chain:*"
        contexts = []

        # SCAN을 사용하여 패턴에 맞는 모든 키 조회
        for key in self.redis_client.scan_iter(match=pattern, count=100):
            data = self.redis_client.get(key)
            if data:
                # JSON 문자열을 딕셔너리로 파싱
                if isinstance(data, str):
                    data_dict = json.loads(data)
                else:
                    data_dict = data

                contexts.append(PipelineContext(**data_dict))  # type: ignore

        if not contexts:
            raise ValueError(f"No contexts found for batch_id: {batch_id}")

        logger.debug(
            f"✅ 배치 컨텍스트 조회: {len(contexts)}개 발견 (batch_id: {batch_id})"
        )
        return contexts

    def delete_context(self, batch_id: str, chain_id: str) -> bool:
        """Context를 Redis에서 삭제

        Args:
            batch_id: 배치 ID
            chain_id: 체인 ID

        Returns:
            삭제 성공 여부
        """
        key = self._get_key(batch_id, chain_id)
        result = self.redis_client.delete(key)
        logger.debug(f"✅ 컨텍스트 삭제: {key}")
        return int(result) > 0  # type: ignore

    def exists(self, batch_id: str, chain_id: str) -> bool:
        """Context 존재 여부 확인

        Args:
            batch_id: 배치 ID
            chain_id: 체인 ID

        Returns:
            존재 여부
        """
        key = self._get_key(batch_id, chain_id)
        return int(self.redis_client.exists(key)) > 0  # type: ignore


# 전역 싱글톤 인스턴스
_pipeline_cache_service: Optional[PipelineCacheService] = None


def get_pipeline_cache_service() -> PipelineCacheService:
    """PipelineCacheService 싱글톤 인스턴스 반환"""
    global _pipeline_cache_service
    if _pipeline_cache_service is None:
        _pipeline_cache_service = PipelineCacheService()
    return _pipeline_cache_service
