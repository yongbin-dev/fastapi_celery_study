# app/api/v1/controllers/tasks_controller.py

from app.core.logging import get_logger
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
from app.api.v1.services import get_model_service, ModelService
from app.utils.response_builder import ResponseBuilder
import httpx

controller = APIRouter()
logging = get_logger(__name__)


@controller.get("/models")
async def get_available_models(service: ModelService = Depends(get_model_service)):

    service._initialize_default_models()
    modelInfo = service.get_model("llama3")

    if modelInfo == None:
        return ResponseBuilder.success()

    logging.info(modelInfo.predict({"prompt": "123"}))
    return ResponseBuilder.success(
        data={},
        message=f"",
    )


@controller.post("/predict")
async def predict(request: PredictRequest):
    return ResponseBuilder.success(
        data={},
        message=f"",
    )
