"""Pipeline Service - 파이프라인 비즈니스 로직

파이프라인 시작, 상태 관리, 취소 등의 비즈니스 로직을 처리합니다.
"""

import uuid

import redis
from shared.core.logging import get_logger
from shared.pipeline import PipelineContext
from shared.schemas.enums import PipelineStatus
from shared.service.redis_service import get_redis_service
from sqlalchemy.orm import Session

from ..schemas.pipeline_schemas import (
    PipelineStartRequest,
    PipelineStartResponse,
    PipelineStatusResponse,
)

logger = get_logger(__name__)


class PipelineService:
    """파이프라인 서비스

    파이프라인 관련 비즈니스 로직을 처리합니다.

    Attributes:
        db: 데이터베이스 세션
        redis_service: Redis 클라이언트
    """

    def __init__(self, db: Session):
        self.db = db
        self.redis_service : redis.Redis = get_redis_service().get_redis_client()

    async def start_pipeline(self, request: PipelineStartRequest) -> PipelineStartResponse:  # noqa: E501
        """파이프라인 시작

        Args:
            request: 파이프라인 시작 요청

        Returns:
            파이프라인 시작 응답
        """
        # 컨텍스트 ID 생성
        context_id = str(uuid.uuid4())

        # 컨텍스트 생성
        context = PipelineContext(
            context_id=context_id,
            status=PipelineStatus.PENDING,
            data={
                "image_path": request.image_path,
                "options": request.options or {}
            }
        )

        # Redis에 컨텍스트 저장
        await self._save_context(context)

        # TODO: Celery 태스크 체인 시작
        # from celery_worker.tasks.pipeline_tasks import start_pipeline_task
        # start_pipeline_task.delay(context_id)

        logger.info(f"파이프라인 시작됨: {context_id}")

        return PipelineStartResponse(
            context_id=context_id,
            status=context.status,
            message="파이프라인이 시작되었습니다"
        )

    async def get_pipeline_status(self, context_id: str) -> PipelineStatusResponse:
        """파이프라인 상태 조회

        Args:
            context_id: 컨텍스트 ID

        Returns:
            파이프라인 상태 정보
        """
        # Redis에서 컨텍스트 조회
        context = await self._get_context(context_id)

        return PipelineStatusResponse(
            context_id=context.context_id,
            status=context.status,
            data=context.data,
            error=context.error
        )

    async def cancel_pipeline(self, context_id: str) -> None:
        """파이프라인 취소

        Args:
            context_id: 컨텍스트 ID
        """
        # Redis에서 컨텍스트 조회
        context = await self._get_context(context_id)
        if not context:
            raise ValueError(f"파이프라인을 찾을 수 없습니다: {context_id}")

        # 상태 업데이트
        context.update_status(PipelineStatus.CANCELLED)
        await self._save_context(context)

        # TODO: Celery 태스크 취소
        # from celery_worker.core.celery_app import app
        # app.control.revoke(task_id, terminate=True)

        logger.info(f"파이프라인 취소됨: {context_id}")

    async def _save_context(self, context: PipelineContext) -> None:
        """컨텍스트를 Redis에 저장"""
        await self.redis_service.set(
            name=f"pipeline:{context.context_id}",
            value=context.model_dump_json(),
            # key=f"pipeline:{context.context_id}",
            # expire=3600  # 1시간 TTL
        )

    async def _get_context(self, context_id: str) -> PipelineContext:
        """Redis에서 컨텍스트 조회"""
        data = await self.redis_service.get(f"pipeline:{context_id}")
        return PipelineContext.model_validate_json(data)
