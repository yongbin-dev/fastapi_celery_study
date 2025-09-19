from fastapi import APIRouter
from app.api.v1.controllers import tasks_controller

api_router = APIRouter()
api_router.include_router(tasks_controller.controller, prefix="/tasks", tags=["tasks"])
