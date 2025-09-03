# app/api/v1/endpoints/tasks_router.py
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession
from ....schemas.tasks import (
    TaskRequest, LongTaskRequest, TaskHistoryResponse,
    AIPipelineRequest, AIPipelineResponse, PipelineStatusResponse
)
from ....dependencies import get_database
from ....schemas.common import ApiResponse
from ....services.task_service import TaskService, get_task_service
from ....utils.response_builder import ResponseBuilder

router = APIRouter()


@router.post("/model-test")
async def image_test_task():
    return ResponseBuilder.success(
        data={
        },
        message=""
    )


@router.post("/example")
async def create_example_task(
        task_request: TaskRequest,
        service: TaskService = Depends(get_task_service)
):
    """예제 태스크 생성"""
    try:
        result = service.create_example_task(
            task_request.message,
            task_request.delay
        )

        return ResponseBuilder.success(
            data=result,
            message="예제 태스크가 생성되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/long-running")
async def create_long_task(
        task_request: LongTaskRequest,
        service: TaskService = Depends(get_task_service)
):
    """긴 시간 소요 태스크 생성"""
    try:
        result = service.create_long_task(task_request.total_steps)

        return ResponseBuilder.success(
            data=result,
            message="긴 시간 소요 태스크가 생성되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_task_status(
        task_id: str,
        service: TaskService = Depends(get_task_service)
):
    """태스크 상태 조회 (ID 검증 포함)"""
    try:
        # 태스크 ID 검증
        if not task_id or len(task_id) < 5:
            raise HTTPException(
                status_code=400,
                detail="Invalid task ID format"
            )

        result = service.get_task_status(task_id)

        return ResponseBuilder.success(
            data=result,
            message="태스크 상태 조회 완료"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str,
                      service: TaskService = Depends(get_task_service)
                      ):
    """태스크 취소"""
    try:
        result = service.cancel_task(task_id)

        return ResponseBuilder.success(
            data=result,
            message="태스크 취소 요청이 전송되었습니다"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_active_tasks(
        service: TaskService = Depends(get_task_service)
):
    """활성 태스크 목록 조회"""
    try:
        result = service.list_active_tasks()

        return ResponseBuilder.success(
            data=result,
            message="활성 태스크 목록 조회 완료"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=ApiResponse[TaskHistoryResponse])
async def get_tasks_history(
        service: TaskService = Depends(get_task_service),
        hours: Optional[int] = Query(1, description="조회할 시간 범위 (시간 단위)", ge=1, le=168),
        status: Optional[str] = Query(None, description="필터링할 상태"),
        task_name: Optional[str] = Query(None, description="필터링할 태스크 이름"),
        limit: Optional[int] = Query(100, description="반환할 최대 결과 수", ge=1, le=1000),
        db: AsyncSession = Depends(get_database)
) -> ApiResponse[TaskHistoryResponse]:
    """기간 내 전체 태스크 히스토리 조회"""
    try:
        result = await service.get_tasks_history(db ,hours, status, task_name, limit )

        return ResponseBuilder.success(
            data=result,
            message=f"지난 {hours}시간 내 태스크 히스토리 조회 완료 "
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"태스크 히스토리 조회 중 오류 발생: {str(e)}")


# AI 파이프라인 엔드포인트들
@router.post("/ai-pipeline", response_model=ApiResponse[AIPipelineResponse])
async def create_ai_pipeline(
        request: AIPipelineRequest,
        service: TaskService = Depends(get_task_service)
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
        service: TaskService = Depends(get_task_service)
) -> ApiResponse[Any]:
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
        service: TaskService = Depends(get_task_service)
):
    """AI 파이프라인 취소"""
    try:
        # 파이프라인 취소 (기존 태스크 취소 로직 재사용)
        result = service.cancel_task(pipeline_id)
        
        return ResponseBuilder.success(
            data=result,
            message="AI 파이프라인 취소 요청이 전송되었습니다"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"파이프라인 취소 중 오류 발생: {str(e)}"
        )
