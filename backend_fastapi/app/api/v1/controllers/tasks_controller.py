# app/api/v1/controllers/tasks_controller.py
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas import (
    AIPipelineRequest, AIPipelineResponse, PipelineStatusResponse,
    PipelineStagesResponse, StageDetailResponse
)
from app.schemas.common import ApiResponse
from app.api.v1.services import get_pipeline_service , get_redis_service
from app.utils.response_builder import ResponseBuilder

controller = APIRouter()

@controller.get("/history", response_model=ApiResponse[list[PipelineStatusResponse]])
async def get_pipeline_history(
        service = Depends(get_pipeline_service),
        db: AsyncSession = Depends(get_db),
        hours: Optional[int] = Query(1, description="조회할 시간 범위 (시간 단위)", ge=1, le=168),
        status: Optional[str] = Query(None, description="필터링할 상태"),
        task_name: Optional[str] = Query(None, description="필터링할 태스크 이름"),
        limit: Optional[int] = Query(100, description="반환할 최대 결과 수", ge=1, le=1000)
) -> ApiResponse[list[PipelineStatusResponse]]:
    result = await service.get_pipeline_history(
        db=db,  hours=hours, status=status, task_name=task_name, limit=limit
    )


    return ResponseBuilder.success(
        data=result,
        message=f"지난 {hours}시간 내 파이프라인 히스토리 조회 완료"
    )


# AI 파이프라인 엔드포인트들
@controller.post("/ai-pipeline", response_model=ApiResponse[AIPipelineResponse])
async def create_ai_pipeline(
        request: AIPipelineRequest,
        service = Depends(get_pipeline_service),
        redis_service = Depends(get_redis_service),
        db: AsyncSession = Depends(get_db),
) -> ApiResponse[AIPipelineResponse]:
    """AI 처리 파이프라인 시작"""
    result = await service.create_ai_pipeline(db=db, redis_service=redis_service, request=request)

    return ResponseBuilder.success(
        data=result,
        message="AI 처리 파이프라인이 시작되었습니다"
    )


# 기존 엔드포인트는 하단의 새로운 배열 기반 엔드포인트로 대체됨

@controller.delete("/ai-pipeline/{chain_id}/cancel")
async def cancel_ai_pipeline(
        chain_id: str,
        service = Depends(get_pipeline_service),
        redis_service = Depends(get_redis_service),
):
    """파이프라인 취소 및 데이터 삭제"""
    result = service.cancel_pipeline(redis_service=redis_service, chain_id=chain_id)

    return ResponseBuilder.success(
        data={
            "chain_id": result["chain_id"],
            "status": result["status"]
        },
        message=result["message"]
    )


@controller.get("/ai-pipeline/{chain_id}/tasks", response_model=ApiResponse[PipelineStagesResponse])
async def get_pipeline_tasks(
        chain_id: str,
        service = Depends(get_pipeline_service),
        redis_service = Depends(get_redis_service),
) -> ApiResponse[PipelineStagesResponse]:
    pipeline_stages = service.get_pipeline_tasks(redis_service=redis_service, chain_id=chain_id)

    return ResponseBuilder.success(
        data=pipeline_stages,
        message=f"체인 '{chain_id}'의 태스크 목록 조회 완료 (총 {pipeline_stages.total_stages}개 스테이지)"
    )



@controller.get("/ai-pipeline/{chain_id}/stage/{stage}", response_model=ApiResponse[StageDetailResponse])
async def get_stage_task(
        chain_id: str,
        stage: int,
        service = Depends(get_pipeline_service),
        redis_service = Depends(get_redis_service),
) -> ApiResponse[StageDetailResponse]:
    stage_detail = service.get_stage_task(redis_service=redis_service, chain_id=chain_id, stage=stage)

    return ResponseBuilder.success(
        data=stage_detail,
        message=f"체인 '{chain_id}'의 단계 {stage} 태스크 상태 조회 완료"
    )