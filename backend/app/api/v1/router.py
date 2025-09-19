from fastapi import APIRouter
from app.api.v1.controllers import pipeline_controller

api_router = APIRouter()
api_router.include_router(
    pipeline_controller.controller, prefix="/tasks", tags=["tasks"]
)
