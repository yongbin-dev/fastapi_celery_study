"""Pipeline Controller - 파이프라인 API 엔드포인트

파이프라인 시작, 상태 조회, 결과 조회 등의 API를 제공합니다.
"""

from fastapi import APIRouter, Depends, HTTPException
from shared.core.database import get_db
from shared.core.logging import get_logger
from sqlalchemy.orm import Session

from ..schemas.pipeline_schemas import (
    PipelineStartRequest,
    PipelineStartResponse,
    PipelineStatusResponse,
)
from ..services.pipeline_service import PipelineService

logger = get_logger(__name__)
router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/start", response_model=PipelineStartResponse)
async def start_pipeline(
    request: PipelineStartRequest,
    db: Session = Depends(get_db)
):
    """파이프라인 시작

    Args:
        request: 파이프라인 시작 요청
        db: 데이터베이스 세션

    Returns:
        파이프라인 시작 응답 (context_id 포함)
    """
    try:
        logger.info(f"파이프라인 시작 요청: {request.model_dump()}")
        service = PipelineService(db)
        result = await service.start_pipeline(request)
        return result
    except Exception as e:
        logger.error(f"파이프라인 시작 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{context_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    context_id: str,
    db: Session = Depends(get_db)
):
    """파이프라인 상태 조회

    Args:
        context_id: 컨텍스트 ID
        db: 데이터베이스 세션

    Returns:
        파이프라인 상태 정보
    """
    try:
        logger.info(f"파이프라인 상태 조회: {context_id}")
        service = PipelineService(db)
        result = await service.get_pipeline_status(context_id)
        if not result:
            raise HTTPException(status_code=404, detail="파이프라인을 찾을 수 없습니다")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파이프라인 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{context_id}")
async def cancel_pipeline(
    context_id: str,
    db: Session = Depends(get_db)
):
    """파이프라인 취소

    Args:
        context_id: 컨텍스트 ID
        db: 데이터베이스 세션

    Returns:
        취소 성공 메시지
    """
    try:
        logger.info(f"파이프라인 취소 요청: {context_id}")
        service = PipelineService(db)
        await service.cancel_pipeline(context_id)
        return {"message": "파이프라인이 취소되었습니다"}
    except Exception as e:
        logger.error(f"파이프라인 취소 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
