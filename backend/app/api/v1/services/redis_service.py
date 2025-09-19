# app/services/redis_service.py

import json
import time
from typing import Dict, Any, List, Optional
import redis
from app.config import settings
from app.core.logging import get_logger
from app.schemas.pipeline import PipelineMetadata
from app.schemas.enums import ProcessStatus
from app.schemas.stage import StageInfo


logger = get_logger(__name__)


class RedisPipelineStatusManager:
    """Redis를 사용한 파이프라인 상태 관리 구현체"""

    def __init__(
        self,
        redis_host: Optional[str] = "",
        redis_port: Optional[int] = 6379,
        redis_db: int = 0,
    ):
        self._redis_client = None
        self.redis_host = redis_host or settings.REDIS_HOST
        self.redis_port = redis_port or settings.REDIS_PORT
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

    def update_status(
        self,
        chain_id: str,
        stage: int,
        status: ProcessStatus,
        metadata: PipelineMetadata,
        progress: Optional[int] = 0,
        task_id: Optional[str] = None,
    ) -> bool:
        """Redis에서 파이프라인 상태 업데이트"""
        try:
            redis_client = self.get_redis_client()

            logger.info(
                f"Pipeline {chain_id}: Stage {stage} - {status.value} ({progress}%)"
            )

            # 기존 파이프라인 데이터 가져오기
            pipeline_data = redis_client.get(chain_id)

            if pipeline_data:
                pipeline_tasks = json.loads(pipeline_data)  # type: ignore
                if not isinstance(pipeline_tasks, list):
                    pipeline_tasks = [pipeline_tasks] if pipeline_tasks else []
            else:
                pipeline_tasks = []

            # 현재 단계의 task 정보 생성
            current_task = {
                "chain_id": chain_id,
                "stage": stage,
                "status": status.value,
                "progress": progress,
                "updated_at": time.time(),
                "metadata": metadata.to_dict(),
            }

            if task_id:
                current_task["task_id"] = task_id

            if (
                status == ProcessStatus.PENDING
                and progress == 0
                and metadata
                and metadata.start_time
            ):
                current_task["started_at"] = metadata.start_time

            # 단계에 해당하는 task가 이미 있는지 확인
            stage_index = None
            for i, task in enumerate(pipeline_tasks):
                if task.get("stage") == stage:
                    stage_index = i
                    break

            if stage_index is not None:
                if (
                    "created_at" not in current_task
                    and "created_at" in pipeline_tasks[stage_index]
                ):
                    current_task["created_at"] = pipeline_tasks[stage_index][
                        "created_at"
                    ]
                if (
                    "started_at" not in current_task
                    and "started_at" in pipeline_tasks[stage_index]
                ):
                    current_task["started_at"] = pipeline_tasks[stage_index][
                        "started_at"
                    ]
                pipeline_tasks[stage_index].update(current_task)
            else:
                if "created_at" not in current_task:
                    current_task["created_at"] = time.time()
                pipeline_tasks.append(current_task)

            # 단계 순서대로 정렬
            pipeline_tasks.sort(key=lambda x: x.get("stage", 0))

            # TTL 설정
            ttl = getattr(settings, "PIPELINE_TTL", 3600)
            redis_client.setex(chain_id, ttl, json.dumps(pipeline_tasks))
            return True

        except Exception as e:
            logger.error(
                f"Redis 파이프라인 상태 업데이트 실패 (Chain: {chain_id}): {e}",
                exc_info=True,
            )
            return False

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

    def initialize_pipeline_stages(self, chain_id: str) -> bool:
        """파이프라인 시작 시 모든 스테이지 정보를 미리 생성"""
        try:
            redis_client = self.get_redis_client()

            from app.pipeline_config import STAGES

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

            ttl = getattr(settings, "PIPELINE_TTL", 3600)
            redis_client.setex(chain_id, ttl, json.dumps(stages_info))

            logger.info(
                f"Pipeline {chain_id}: 전체 스테이지 정보 초기화 완료 ({len(stages)}단계)"
            )
            return True

        except Exception as e:
            logger.error(
                f"Pipeline {chain_id}: 스테이지 초기화 실패 - {e}", exc_info=True
            )
            return False


def get_redis_service() -> RedisPipelineStatusManager:
    return RedisPipelineStatusManager()
