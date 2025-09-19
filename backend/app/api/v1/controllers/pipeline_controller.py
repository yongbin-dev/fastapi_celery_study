# app/api/v1/controllers/tasks_controller.py
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.core.database import get_db
from app.schemas import (
    AIPipelineRequest,
    AIPipelineResponse,
    PredictResponse,
    PredictRequest,
)
from app.schemas.chain_execution import ChainExecutionResponse
from app.schemas.common import ApiResponse
from app.api.v1.services import get_pipeline_service, get_redis_service
from app.utils.response_builder import ResponseBuilder
import httpx

controller = APIRouter()

# Ollama 서버 설정

# 실제 확인된 설정
OLLAMA_SERVERS = {
    "server1": {"url": "http://192.168.0.122:12434", "name": "qwen3-server"},
    "server2": {"url": "http://192.168.0.122:13434", "name": "qwen2-server"},
}

# 두 서버 모두 동일한 모델 보유
AVAILABLE_MODELS = ["qwen2.5vl:7b-q8_0", "qwen3:32b", "mistral-small3.2:24b"]


@controller.get("/models")
async def get_available_models():
    return ResponseBuilder.success(
        data={"servers": OLLAMA_SERVERS, "available_models": AVAILABLE_MODELS},
        message=f"",
    )


@controller.post("/predict", response_model=ApiResponse[PredictResponse])
async def predict(request: PredictRequest):
    if request.server not in OLLAMA_SERVERS:
        return {
            "message": f"지원하지 않는 서버: {request.server}",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "data": {"available_servers": list(OLLAMA_SERVERS.keys())},
        }

    if request.model not in AVAILABLE_MODELS:
        return {
            "message": f"지원하지 않는 모델: {request.model}",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "data": {"available_models": AVAILABLE_MODELS},
        }

    server_info = OLLAMA_SERVERS[request.server]
    ollama_url = server_info["url"]

    logging.info(f"Server: {server_info['name']} ({ollama_url})")
    logging.info(f"Model: {request.model}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{ollama_url}/api/generate",
            json={"model": request.model, "prompt": request.prompt, "stream": False},
        )

        logging.info(f"Response Status Code: {response}")

        if response.status_code == 200:
            result = response.json()
            return ResponseBuilder.success(data=result)


@controller.get("/history", response_model=ApiResponse[list[ChainExecutionResponse]])
async def get_pipeline_history(
    service=Depends(get_pipeline_service),
    db: AsyncSession = Depends(get_db),
    hours: Optional[int] = Query(
        1, description="조회할 시간 범위 (시간 단위)", ge=1, le=168
    ),
    status: Optional[str] = Query(None, description="필터링할 상태"),
    task_name: Optional[str] = Query(None, description="필터링할 태스크 이름"),
    limit: Optional[int] = Query(100, description="반환할 최대 결과 수", ge=1, le=1000),
) -> ApiResponse[list[ChainExecutionResponse]]:
    result = await service.get_pipeline_history(
        db=db, hours=hours, status=status, task_name=task_name, limit=limit
    )

    return ResponseBuilder.success(
        data=result, message=f"지난 {hours}시간 내 파이프라인 히스토리 조회 완료"
    )


# AI 파이프라인 엔드포인트들
@controller.post("/ai-pipeline", response_model=ApiResponse[AIPipelineResponse])
async def create_ai_pipeline(
    request: AIPipelineRequest,
    service=Depends(get_pipeline_service),
    redis_service=Depends(get_redis_service),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AIPipelineResponse]:
    """AI 처리 파이프라인 시작"""
    result = await service.create_ai_pipeline(
        db=db, redis_service=redis_service, request=request
    )

    return ResponseBuilder.success(
        data=result, message="AI 처리 파이프라인이 시작되었습니다"
    )


# 기존 엔드포인트는 하단의 새로운 배열 기반 엔드포인트로 대체됨


@controller.delete("/ai-pipeline/{chain_id}/cancel")
async def cancel_ai_pipeline(
    chain_id: str,
    service=Depends(get_pipeline_service),
    redis_service=Depends(get_redis_service),
):
    """파이프라인 취소 및 데이터 삭제"""
    result = service.cancel_pipeline(redis_service=redis_service, chain_id=chain_id)

    return ResponseBuilder.success(
        data={"chain_id": result["chain_id"], "status": result["status"]},
        message=result["message"],
    )


@controller.get(
    "/ai-pipeline/{chain_id}/tasks",
    response_model=ApiResponse[ChainExecutionResponse],
)
async def get_pipeline_tasks(
    chain_id: str,
    service=Depends(get_pipeline_service),
    db=Depends(get_db),
) -> ApiResponse[ChainExecutionResponse]:
    pipeline_stages = await service.get_pipeline_tasks(db=db, chain_id=chain_id)

    return ResponseBuilder.success(
        data=pipeline_stages,
        message=f"체인 '{chain_id}'의 태스크 목록 조회 완료 (총 개 스테이지)",
    )
