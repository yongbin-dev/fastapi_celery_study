# app/api/v1/endpoints/tasks_router.py
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.params import Query

from ....schemas import (
    AIPipelineRequest, AIPipelineResponse, PipelineStatusResponse,
    PipelineStagesResponse, StageDetailResponse
)
from ....schemas.common import ApiResponse
from ....services.pipeline_service import PipelineService, get_pipeline_service
from ....utils.response_builder import ResponseBuilder

router = APIRouter()


@router.post("/model-test")
async def image_test_task():
    return ResponseBuilder.success(
        data={
        },
        message=""
    )


@router.get("/history", response_model=ApiResponse[list[PipelineStatusResponse]])
async def get_pipeline_history(
        service: PipelineService = Depends(get_pipeline_service),
        hours: Optional[int] = Query(1, description="조회할 시간 범위 (시간 단위)", ge=1, le=168),
        status: Optional[str] = Query(None, description="필터링할 상태"),
        task_name: Optional[str] = Query(None, description="필터링할 태스크 이름"),
        limit: Optional[int] = Query(100, description="반환할 최대 결과 수", ge=1, le=1000)
) -> ApiResponse[list[PipelineStatusResponse]]:
    result = await service.get_pipeline_history(hours=hours, status=status, task_name=task_name, limit=limit)

    data_source = "Redis" if hours <= 1 else "DB"
    return ResponseBuilder.success(
        data=result,
        message=f"지난 {hours}시간 내 파이프라인 히스토리 조회 완료 ({data_source} 기반)"
    )


# AI 파이프라인 엔드포인트들
@router.post("/ai-pipeline", response_model=ApiResponse[AIPipelineResponse])
async def create_ai_pipeline(
        request: AIPipelineRequest,
        service: PipelineService = Depends(get_pipeline_service),
) -> ApiResponse[AIPipelineResponse]:
    """AI 처리 파이프라인 시작"""
    result = await service.create_ai_pipeline(request)

    return ResponseBuilder.success(
        data=result,
        message="AI 처리 파이프라인이 시작되었습니다"
    )


# 기존 엔드포인트는 하단의 새로운 배열 기반 엔드포인트로 대체됨

@router.delete("/ai-pipeline/{chain_id}/cancel")
async def cancel_ai_pipeline(
        chain_id: str,
        service: PipelineService = Depends(get_pipeline_service)
):
    """파이프라인 취소 및 데이터 삭제"""
    result = service.cancel_pipeline(chain_id)
    
    return ResponseBuilder.success(
        data={
            "chain_id": result["chain_id"],
            "status": result["status"]
        },
        message=result["message"]
    )


@router.get("/ai-pipeline/{chain_id}/tasks", response_model=ApiResponse[PipelineStagesResponse])
async def get_pipeline_tasks(
        chain_id: str,
        service: PipelineService = Depends(get_pipeline_service)
) -> ApiResponse[PipelineStagesResponse]:
    """파이프라인 전체 태스크 목록 조회 (구조화된 스키마)"""
    pipeline_stages = service.get_pipeline_tasks(chain_id)
    
    return ResponseBuilder.success(
        data=pipeline_stages,
        message=f"체인 '{chain_id}'의 태스크 목록 조회 완료 (총 {pipeline_stages.total_stages}개 스테이지)"
    )


@router.get("/ai-pipeline/{chain_id}/stage/{stage}", response_model=ApiResponse[StageDetailResponse])
async def get_stage_task(
        chain_id: str,
        stage: int,
        service: PipelineService = Depends(get_pipeline_service)
) -> ApiResponse[StageDetailResponse]:
    """특정 단계의 태스크 상태 조회 (구조화된 스키마)"""
    stage_detail = service.get_stage_task(chain_id, stage)

    return ResponseBuilder.success(
        data=stage_detail,
        message=f"체인 '{chain_id}'의 단계 {stage} 태스크 상태 조회 완료"
    )
