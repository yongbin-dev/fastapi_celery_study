from fastapi import Depends, HTTPException, status, Query
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db


def validate_task_id(task_id: str) -> str:
    """태스크 ID 검증"""
    if not task_id or len(task_id) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )
    return task_id


def validate_pagination(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기")
) -> Dict[str, int]:
    """페이지네이션 검증"""
    return {"page": page, "size": size}


def validate_history_params(
    hours: int = Query(1, ge=1, le=168, description="조회 시간 범위 (시간)"),
    status: Optional[str] = Query(None, description="필터링할 상태"),
    task_name: Optional[str] = Query(None, description="필터링할 태스크 이름"),
    limit: int = Query(100, ge=1, le=1000, description="최대 결과 수")
) -> Dict[str, Any]:
    """태스크 히스토리 조회 파라미터 검증"""
    valid_statuses = ["SUCCESS", "FAILURE", "PENDING", "PROGRESS", "REVOKED"]
    
    if status and status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    return {
        "hours": hours,
        "status": status,
        "task_name": task_name,
        "limit": limit
    }


def get_current_model(model_name: str = "default"):
    """현재 모델 의존성"""
    def _get_model():
        model = model_service.get_model(model_name)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_name} not found"
            )
        return model
    return _get_model


async def get_database() -> AsyncSession:
    """
    데이터베이스 세션 의존성
    FastAPI 엔드포인트에서 다음과 같이 사용:
    async def some_endpoint(db: AsyncSession = Depends(get_database)):
    """
    async for session in get_db():
        yield session