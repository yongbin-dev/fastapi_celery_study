# app/api/v1/endpoints/tasks_router.py
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession
from ....schemas.common import ApiResponse
from ....schemas import (
    AIPipelineRequest, AIPipelineResponse, PipelineStatusResponse
)
from ....core.database import get_db
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
        db: AsyncSession = Depends(get_db),
        hours: Optional[int] = Query(1, description="조회할 시간 범위 (시간 단위)", ge=1, le=168),
        status: Optional[str] = Query(None, description="필터링할 상태"),
        task_name: Optional[str] = Query(None, description="필터링할 태스크 이름"),
        limit: Optional[int] = Query(100, description="반환할 최대 결과 수", ge=1, le=1000)
) -> ApiResponse[list[PipelineStatusResponse]]:
    """
    태스크 히스토리 조회
    - 1시간 이내: Redis에서 실시간 조회
    - 1시간 초과: DB에서 영구 데이터 조회
    """
    try:
        result = await service.get_pipeline_history(db, hours, status, task_name, limit)

        data_source = "Redis" if hours <= 1 else "DB"
        return ResponseBuilder.success(
            data=result,
            message=f"지난 {hours}시간 내 파이프라인 히스토리 조회 완료 ({data_source} 기반)"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"태스크 히스토리 조회 중 오류 발생: {str(e)}")


# AI 파이프라인 엔드포인트들
@router.post("/ai-pipeline", response_model=ApiResponse[AIPipelineResponse])
async def create_ai_pipeline(
        request: AIPipelineRequest,
        service: PipelineService = Depends(get_pipeline_service)
) -> ApiResponse[AIPipelineResponse]:
    """AI 처리 파이프라인 시작"""
    try:
        result = service.create_ai_pipeline(request)
        
        return ResponseBuilder.success(
            data=result,
            message="AI 처리 파이프라인이 시작되었습니다"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"파이프라인 생성 중 오류 발생: {str(e)}"
        )


@router.get("/ai-pipeline/{pipeline_id}/status", response_model=ApiResponse[PipelineStatusResponse])
async def get_pipeline_status(
        pipeline_id: str,
        service: PipelineService = Depends(get_pipeline_service)
) -> ApiResponse[PipelineStatusResponse]:
    """AI 파이프라인 진행 상태 조회"""
    try:
        # 파이프라인 ID 검증
        if not pipeline_id or len(pipeline_id) < 5:
            raise HTTPException(
                status_code=400,
                detail="유효하지 않은 파이프라인 ID 형식입니다"
            )
        
        result = service.get_pipeline_status(pipeline_id)
        return ResponseBuilder.success(
            data=result,
            message=f""
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"파이프라인 상태 조회 중 오류 발생: {str(e)}"
        )


@router.delete("/ai-pipeline/{pipeline_id}/cancel")
async def cancel_ai_pipeline(
        pipeline_id: str,
        service: PipelineService = Depends(get_pipeline_service)
):
    """AI 파이프라인 취소"""
    try:
        # Celery 태스크 취소
        from ....core.celery_app import celery_app
        celery_app.control.revoke(pipeline_id, terminate=True)
        
        # Redis에서 파이프라인 상태 업데이트
        pipeline_key = f"pipeline:{pipeline_id}"
        pipeline_data = service.redis_client.get(pipeline_key)
        if pipeline_data:
            import json
            state_info = json.loads(pipeline_data)
            state_info["status"] = "REVOKED"
            service.redis_client.setex(pipeline_key, 3600, json.dumps(state_info))
        
        return ResponseBuilder.success(
            data={"pipeline_id": pipeline_id, "status": "REVOKED"},
            message="AI 파이프라인 취소 요청이 전송되었습니다"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"파이프라인 취소 중 오류 발생: {str(e)}"
        )
