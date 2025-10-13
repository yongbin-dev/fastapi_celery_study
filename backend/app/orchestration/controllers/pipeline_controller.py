# app/orchestration/controllers/pipeline_controller.py
"""
파이프라인 오케스트레이션 API

여러 도메인을 조합한 워크플로우를 실행하고 관리합니다.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.core.logging import get_logger
from app.core.supabase import get_supabase_async
from app.orchestration.schemas.chain_execution import ChainExecutionResponse
from app.orchestration.services import PipelineService, get_pipeline_service
from app.schemas.common import ApiResponse
from app.shared.redis_service import RedisService, get_redis_service
from app.utils.response_builder import ResponseBuilder

from ..schemas import AIPipelineRequest, AIPipelineResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])


@router.get("/history", response_model=ApiResponse[list[ChainExecutionResponse]])
async def get_pipeline_history(
    service: PipelineService = Depends(get_pipeline_service),
    db: Client = Depends(get_supabase_async),
    hours: Optional[int] = Query(
        1, description="조회할 시간 범위 (시간 단위)", ge=1, le=168
    ),
    status: Optional[str] = Query(None, description="필터링할 상태"),
    task_name: Optional[str] = Query(None, description="필터링할 태스크 이름"),
    limit: Optional[int] = Query(100, description="반환할 최대 결과 수", ge=1, le=1000),
) -> ApiResponse[list[ChainExecutionResponse]]:
    """
    파이프라인 실행 히스토리 조회

    - **hours**: 조회할 시간 범위
    - **status**: 필터링할 상태 (선택)
    - **task_name**: 필터링할 태스크 이름 (선택)
    - **limit**: 최대 결과 수
    """
    result = await service.get_pipeline_history(
        db=db, hours=hours, status=status, task_name=task_name, limit=limit
    )

    return ResponseBuilder.success(
        data=result, message=f"지난 {hours}시간 내 파이프라인 히스토리 조회 완료"
    )


@router.post("/ai-pipeline", response_model=ApiResponse[AIPipelineResponse])
async def create_ai_pipeline(
    request: AIPipelineRequest,
    service: PipelineService = Depends(get_pipeline_service),
    redis_service: RedisService = Depends(get_redis_service),
    db: Client = Depends(get_supabase_async),
) -> ApiResponse[AIPipelineResponse]:
    """
    AI 처리 파이프라인 시작

    여러 AI 도메인(OCR, LLM, Vision)을 조합한 복잡한 워크플로우를 실행합니다.

    - **text**: 입력 텍스트
    - **options**: 추가 옵션
    - **priority**: 우선순위 (1-10)
    - **callback_url**: 완료 시 콜백 URL (선택)
    """
    result = await service.create_ai_pipeline(
        db=db, redis_service=redis_service, request=request
    )

    return ResponseBuilder.success(
        data=result, message="AI 처리 파이프라인이 시작되었습니다"
    )


@router.get(
    "/ai-pipeline/{chain_id}/tasks",
    response_model=ApiResponse[ChainExecutionResponse],
)
async def get_pipeline_tasks(
    chain_id: str,
    service: PipelineService = Depends(get_pipeline_service),
    db: Client = Depends(get_supabase_async),
) -> ApiResponse[ChainExecutionResponse]:
    """
    파이프라인 태스크 목록 조회

    특정 파이프라인의 모든 태스크 실행 상태를 조회합니다.

    - **chain_id**: 파이프라인 실행 ID
    """
    pipeline_stages = await service.get_pipeline_tasks(db=db, chain_id=chain_id)

    return ResponseBuilder.success(
        data=pipeline_stages,
        message=f"체인 '{chain_id}'의 태스크 목록 조회 완료",
    )


@router.delete("/ai-pipeline/{chain_id}/cancel")
async def cancel_ai_pipeline(
    chain_id: str,
    service: PipelineService = Depends(get_pipeline_service),
    redis_service: RedisService = Depends(get_redis_service),
):
    """
    파이프라인 취소 및 데이터 삭제

    실행 중이거나 완료된 파이프라인을 취소하고 관련 데이터를 삭제합니다.

    - **chain_id**: 파이프라인 실행 ID
    """
    result = service.cancel_pipeline(redis_service=redis_service, chain_id=chain_id)

    return ResponseBuilder.success(
        data={"chain_id": result["chain_id"], "status": result["status"]},
        message=result["message"],
    )
