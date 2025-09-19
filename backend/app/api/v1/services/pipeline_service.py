# services/pipeline_service.py

import uuid
from typing import Optional, Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)
from celery import chain
from fastapi import HTTPException, Depends

from app.models.chain_execution import ChainExecution
from app.schemas import AIPipelineRequest, AIPipelineResponse, ChainExecutionResponse
from app.api.v1.crud import (
    async_chain_execution as chain_execution_crud,
)

from app.api.v1.services.redis_service import RedisPipelineStatusManager
from sqlalchemy.ext.asyncio import AsyncSession


class PipelineService:
    def _validate_chain_id(self, chain_id: str) -> None:
        """체인 ID 유효성 검증"""
        if not chain_id or len(chain_id) < 5:
            raise HTTPException(
                status_code=400, detail="유효하지 않은 체인 ID 형식입니다"
            )

    def _validate_stage(self, stage: int) -> None:
        """스테이지 번호 유효성 검증"""
        if stage < 1 or stage > 4:
            raise HTTPException(
                status_code=400, detail="단계는 1~4 사이의 값이어야 합니다"
            )

    async def get_pipeline_history(
        self,
        db: AsyncSession,
        hours: int = 1,
        status: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[ChainExecutionResponse]:
        """파이프라인 히스토리 조회 - DB 기반"""

        chain_executions = await chain_execution_crud.get_multi_with_task_logs(
            db, days=hours // 24 + 1, limit=limit
        )

        return [ChainExecutionResponse.model_validate(ce) for ce in chain_executions]

    async def create_ai_pipeline(
        self,
        db: AsyncSession,
        redis_service: RedisPipelineStatusManager,
        request: AIPipelineRequest,
    ) -> AIPipelineResponse:
        """AI 처리 파이프라인 시작"""
        input_data = {
            "text": request.text,
            "options": request.options,
            "priority": request.priority,
            "callback_url": request.callback_url,
        }

        try:
            chain_id = str(uuid.uuid4())

            # 1. ChainExecution 테이블에 레코드 생성
            chain_execution = ChainExecution(
                chain_name="ai_processing_pipeline",
                total_tasks=4,  # 4단계 파이프라인
                initiated_by=getattr(request, "user_id", "system"),
                input_data=input_data,
                chain_id=chain_id,
            )

            db.add(chain_execution)
            await db.commit()
            await db.refresh(chain_execution)

            logger.info(
                f"ChainExecution created with ID: {chain_execution.id}, chain_id: {chain_execution.chain_id}"
            )

            # 2. 전체 스테이지 정보를 Redis에 미리 저장
            chain_id_str = str(chain_execution.chain_id)
            stages_initialized = redis_service.initialize_pipeline_stages(chain_id_str)

            if not stages_initialized:
                await db.rollback()
                logger.error(f"Pipeline {chain_id_str}: 스테이지 초기화 실패")
                raise HTTPException(
                    status_code=500, detail="파이프라인 스테이지 초기화에 실패했습니다"
                )

            from app.core.celery.celery_tasks import (
                stage1_preprocessing,
                stage2_feature_extraction,
                stage3_model_inference,
                stage4_post_processing,
            )

            pipeline_chain = chain(
                stage1_preprocessing.s(chain_id_str, input_data),  # type: ignore[misc]
                stage2_feature_extraction.s(),  # type: ignore[misc]
                stage3_model_inference.s(),  # type: ignore[misc]
                stage4_post_processing.s(),  # type: ignore[misc]
            )

            pipeline_chain.apply_async()

            chain_execution.start_execution()
            await db.commit()

            return AIPipelineResponse(
                pipeline_id=str(chain_execution.chain_id),  # Celery task ID
                status="STARTED",
                message="AI 처리 파이프라인이 시작되었습니다",
                estimated_duration=20,  # 예상 20초
            )

        except Exception as e:
            # 데이터베이스 에러, Redis 연결 에러 등 예상치 못한 에러
            await db.rollback()
            logger.error(
                f"파이프라인 생성 중 예상치 못한 에러 발생: {str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="AI 파이프라인 시작 중 내부 서버 오류가 발생했습니다",
            )

    async def get_pipeline_tasks(
        self, db: AsyncSession, chain_id: str
    ) -> ChainExecutionResponse:
        """파이프라인 전체 태스크 목록 조회 (구조화된 응답)"""
        # 체인 ID 검증
        self._validate_chain_id(chain_id)

        # Redis에서 파이프라인 태스크 목록 조회
        chain_execution = await chain_execution_crud.get_with_task_logs(
            db, chain_id=chain_id
        )

        if not chain_execution:
            raise HTTPException(
                status_code=404,
                detail=f"체인 ID '{chain_id}'에 Pydantic해당하는 파이프라인을 찾을 수 없습니다",
            )

        # ChainExecution 객체를 ChainExecutionResponse 스키마로 변환
        return ChainExecutionResponse.model_validate(chain_execution)

    def cancel_pipeline(
        self, redis_service: RedisPipelineStatusManager, chain_id: str
    ) -> Dict[str, str]:
        """파이프라인 취소 및 데이터 삭제"""
        # Redis에서 파이프라인 데이터 삭제
        deleted = redis_service.delete_pipeline(chain_id)

        if deleted:
            return {
                "chain_id": chain_id,
                "status": "DELETED",
                "message": "AI 파이프라인 취소 및 데이터 삭제가 완료되었습니다",
            }
        else:
            return {
                "chain_id": chain_id,
                "status": "NOT_FOUND",
                "message": "파이프라인 데이터를 찾을 수 없어 취소만 수행되었습니다",
            }


pipeline_service_instance = PipelineService()


def get_pipeline_service() -> PipelineService:
    return pipeline_service_instance
