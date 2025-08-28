from fastapi import APIRouter
from .endpoints import tasks_router , users_router

api_router = APIRouter()
api_router.include_router(users_router.router, prefix="/users", tags=["users"])
api_router.include_router(tasks_router.router, prefix="/tasks", tags=["tasks"])
