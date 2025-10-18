# app/orchestration/services/pipeline_service.py
"""
파이프라인 오케스트레이션 서비스

여러 도메인을 조합한 복잡한 워크플로우를 관리합니다.
"""

import uuid
from typing import Dict, List, Optional

from fastapi import HTTPException
from shared.core.logging import get_logger
from shared.repository.crud.async_crud import chain_execution_crud
from shared.schemas import (
    AIPipelineRequest,
    AIPipelineResponse,
    ChainExecutionResponse,
)
from shared.schemas.enums import ProcessStatus
from shared.service.redis_service import RedisService
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class PipelineService:
    """파이프라인 오케스트레이션 서비스"""

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
        hours: Optional[int] = None,
        status: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ChainExecutionResponse]:
        """파이프라인 히스토리 조회 -  기반"""
        hours_value = hours or 1
        limit_value = limit or 100

        chain_executions = await chain_execution_crud.get_multi_with_task_logs(
            db, days=hours_value // 24 + 1, limit=limit_value
        )

        return [ChainExecutionResponse.model_validate(ce) for ce in chain_executions]

    async def create_ai_pipeline(
        self,
        db: AsyncSession,
        redis_service: RedisService,
        request: AIPipelineRequest,
    ) -> AIPipelineResponse:
        """
        AI 처리 파이프라인 시작

        여러 도메인(OCR, LLM, Vision)을 조합한 파이프라인을 실행합니다.
        """
        input_data = {
            "text": request.text,
            "options": request.options,
            "priority": request.priority,
            "callback_url": request.callback_url,
        }

        chain_id = str(uuid.uuid4())

        chain_execution = await chain_execution_crud.create_chain_execution(
            db,
            chain_id=chain_id,
            chain_name="ai_processing_pipeline",
            total_tasks=4,  # 4단계 파이프라인
            initiated_by=getattr(request, "user_id", "system"),
            input_data=input_data,
        )

        # 2. Redis에 스테이지 정보 초기화
        chain_id_str = str(chain_execution.chain_id)
        stages_initialized = redis_service.initialize_pipeline_stages(chain_id_str)

        if not stages_initialized:
            # 는 자동 롤백이 없으므로 에러만 로깅
            logger.error(f"Pipeline {chain_id_str}: 스테이지 초기화 실패")
            raise HTTPException(
                status_code=500, detail="파이프라인 스테이지 초기화에 실패했습니다"
            )

        # 3. 파이프라인 워크플로우 생성 및 실행
        # pipeline_chain = create_ai_processing_pipeline(chain_id_str, input_data)
        # pipeline_chain.apply_async()

        # 4. 체인 실행 시작 상태로 업데이트
        await chain_execution_crud.update_status(
            db,
            chain_execution=chain_execution,
            status=ProcessStatus.STARTED,
        )

        return AIPipelineResponse(
            pipeline_id=chain_id_str,
            status="STARTED",
            message="AI 처리 파이프라인이 시작되었습니다",
            estimated_duration=20,
        )

    async def get_pipeline_tasks(
        self, db: AsyncSession, chain_id: str
    ) -> ChainExecutionResponse:
        """파이프라인 전체 태스크 목록 조회 -  기반"""
        self._validate_chain_id(chain_id)

        chain_execution = await chain_execution_crud.get_with_task_logs(
            db, chain_id=chain_id
        )

        if not chain_execution:
            raise HTTPException(
                status_code=404,
                detail=f"체인 ID '{chain_id}'에 해당하는 파이프라인을 찾을 수 없습니다",
            )

        return ChainExecutionResponse.model_validate(chain_execution)

    def cancel_pipeline(
        self, redis_service: RedisService, chain_id: str
    ) -> Dict[str, str]:
        """파이프라인 취소 및 데이터 삭제"""
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


# 싱글톤 인스턴스
pipeline_service_instance = PipelineService()


def get_pipeline_service() -> PipelineService:
    """파이프라인 서비스 의존성 주입"""
    return pipeline_service_instance
