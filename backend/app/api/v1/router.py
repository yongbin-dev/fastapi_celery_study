from fastapi import APIRouter
from app.api.v1.controllers import pipeline_controller
from app.api.v1.controllers import model_controller

api_router = APIRouter()

api_router.include_router(
    pipeline_controller.controller, prefix="/tasks", tags=["tasks"]
)
api_router.include_router(model_controller.controller, prefix="/model", tags=["model"])
