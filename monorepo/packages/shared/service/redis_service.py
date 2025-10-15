# app/services/redis_service.py

import json

import redis

from ..config.pipeline_config import STAGES
from ..core.logging import get_logger
from ..schemas.stage import StageInfo

logger = get_logger(__name__)


class RedisService:
    """Redis를 사용한 파이프라인 상태 관리 구현체"""

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

    def delete_pipeline(self, chain_id: str) -> bool:
        """파이프라인 데이터 삭제"""
        try:
            redis_client = self.get_redis_client()
            result = redis_client.delete(chain_id)
            logger.info(
                f"Pipeline {chain_id} 데이터 삭제 {'completed' if result else 'failed'}"
            )
            return bool(result)
        except Exception as e:
            logger.error(
                f"Redis 파이프라인 데이터 삭제 실패 (Chain: {chain_id}): {e}",
                exc_info=True,
            )
            return False

    def initialize_pipeline_stages(
        self, chain_id: str, pipeline_ttl: int = 3600
    ) -> bool:
        """파이프라인 시작 시 모든 스테이지 정보를 미리 생성"""
        try:
            redis_client = self.get_redis_client()

            stages = []
            for stage_config in STAGES:
                stages.append(
                    StageInfo.create_pending_stage(
                        chain_id=chain_id,
                        stage=stage_config["stage"],
                        stage_name=stage_config["name"],
                        description=stage_config["description"],
                        expected_duration=stage_config["expected_duration"],
                    )
                )

            stages_info = [stage.to_dict() for stage in stages]

            redis_client.setex(chain_id, pipeline_ttl, json.dumps(stages_info))

            return True

        except Exception as e:
            logger.error(
                f"Pipeline {chain_id}: 스테이지 초기화 실패 - {e}", exc_info=True
            )
            return False


def get_redis_service():
    return RedisService(redis_host="localhost", redis_port=6379, redis_db=0)
